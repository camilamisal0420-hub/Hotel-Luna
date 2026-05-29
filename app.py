from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import mysql.connector
from datetime import date as date_type
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'super-secret-key-hotel-luna-2026'

# ================== DATABASE CONNECTION ==================
def get_db():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='hotel_luna'
    )

# ================== LANDING PAGE ==================
@app.route('/')
def landing():
    return render_template('landing.html')

# ================== SIGN IN ==================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
            user = cursor.fetchone()
            if user:
                session['user_id'] = user['id']
                session['user_name'] = user['full_name']
                session['is_admin'] = user.get('is_admin', 0)
                flash(f'Welcome back, {user["full_name"]}!', 'success')
                if session['is_admin'] == 1:
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('dashboard'))
            else:
                flash('Invalid email or password.', 'error')
        except Exception as e:
            flash(f'Database error: {str(e)}', 'error')
        finally:
            conn.close()
    return render_template('signin.html')

# ================== SIGN UP ==================
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('signup.html')
        if not full_name or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('signup.html')
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (full_name, email, password) VALUES (%s, %s, %s)",
                           (full_name, email, password))
            conn.commit()
            flash('Account created! Please sign in.', 'success')
            return redirect(url_for('login'))
        except mysql.connector.IntegrityError:
            flash('Email already registered.', 'error')
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
        finally:
            conn.close()
    return render_template('signup.html')

# ================== LOGOUT ==================
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('landing'))

# ================== USER DASHBOARD ==================
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('login'))
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    rooms = []
    bookings = []
    try:
        cursor.execute("SELECT * FROM rooms ORDER BY name ASC")
        rooms = cursor.fetchall()
        cursor.execute("""
            SELECT r.id, r.guest_name, r.date, r.time_slot, r.status, ro.name AS room_name
            FROM reservations r
            JOIN rooms ro ON r.room_id = ro.id
            WHERE r.user_id = %s
            ORDER BY r.date ASC, r.time_slot ASC
        """, (user_id,))
        bookings = cursor.fetchall()
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
    finally:
        conn.close()
    today = date_type.today().isoformat()
    return render_template('user_dashboard.html',
                           user={'name': session['user_name']},
                           rooms=rooms,
                           bookings=bookings,
                           today=today)

# ================== AJAX: GET TIME SLOTS FOR A ROOM ==================
@app.route('/get_room_slots')
def get_room_slots():
    room_id = request.args.get('room_id')
    date = request.args.get('date', '')
    if not room_id:
        return jsonify([])
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT time_slot AS slot FROM room_time_slots 
            WHERE room_id = %s AND is_available = TRUE 
            ORDER BY time_slot ASC
        """, (room_id,))
        slots = [row['slot'] for row in cursor.fetchall()]
        
        if date:
            cursor.execute("""
                SELECT time_slot FROM reservations 
                WHERE room_id = %s AND date = %s AND status != 'cancelled'
            """, (room_id, date))
            booked_slots = [row['time_slot'] for row in cursor.fetchall()]
            slots = [s for s in slots if s not in booked_slots]
        
        return jsonify([{'slot': s} for s in slots])
    except Exception as e:
        print(e)
        return jsonify([])
    finally:
        conn.close()

# ================== CREATE RESERVATION ==================
@app.route('/create_reservation', methods=['POST'])
def create_reservation():
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('login'))
    
    guest_name = request.form['guest_name']
    date = request.form['date']
    time_slot = request.form['time_slot']
    room_id = request.form.get('room_id')
    user_id = session['user_id']
    
    try:
        booking_date = date_type.fromisoformat(date)
        if booking_date < date_type.today():
            flash('Cannot book a past date.', 'error')
            return redirect(url_for('dashboard'))
    except ValueError:
        flash('Invalid date format.', 'error')
        return redirect(url_for('dashboard'))
    
    if not room_id:
        flash('Please select a room.', 'error')
        return redirect(url_for('dashboard'))
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT is_available FROM room_time_slots 
            WHERE room_id = %s AND time_slot = %s
        """, (room_id, time_slot))
        slot_info = cursor.fetchone()
        if not slot_info:
            flash('Invalid time slot for this room.', 'error')
            return redirect(url_for('dashboard'))
        if not slot_info['is_available']:
            flash('This time slot is currently disabled for this room.', 'error')
            return redirect(url_for('dashboard'))
        
        cursor.execute("""
            SELECT COUNT(*) AS cnt FROM reservations
            WHERE room_id = %s AND date = %s AND time_slot = %s AND status != 'cancelled'
        """, (room_id, date, time_slot))
        count = cursor.fetchone()['cnt']
        if count > 0:
            flash('This time slot is already booked for the selected room.', 'error')
            return redirect(url_for('dashboard'))
        
        cursor.execute("""
            INSERT INTO reservations (user_id, room_id, guest_name, date, time_slot, status)
            VALUES (%s, %s, %s, %s, %s, 'confirmed')
        """, (user_id, room_id, guest_name, date, time_slot))
        conn.commit()
        flash('Reservation created successfully!', 'success')
    except Exception as e:
        flash(f'Error creating reservation: {str(e)}', 'error')
    finally:
        conn.close()
    return redirect(url_for('dashboard'))

# ================== CANCEL RESERVATION (USER) ==================
@app.route('/cancel_reservation/<int:reservation_id>', methods=['POST'])
def cancel_reservation(reservation_id):
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('login'))
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE reservations SET status = 'cancelled'
            WHERE id = %s AND user_id = %s
        """, (reservation_id, session['user_id']))
        if cursor.rowcount == 0:
            flash('Reservation not found or you are not authorized.', 'error')
        else:
            conn.commit()
            flash('Reservation cancelled.', 'success')
    except Exception as e:
        flash(f'Error cancelling reservation: {str(e)}', 'error')
    finally:
        conn.close()
    return redirect(url_for('dashboard'))

# ================== MY BOOKINGS PAGE ==================
@app.route('/my_bookings')
def my_bookings():
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('login'))
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    bookings = []
    try:
        cursor.execute("""
            SELECT r.id, r.guest_name, r.date, r.time_slot, r.status, ro.name AS room_name
            FROM reservations r
            JOIN rooms ro ON r.room_id = ro.id
            WHERE r.user_id = %s
            ORDER BY r.date ASC, r.time_slot ASC
        """, (user_id,))
        bookings = cursor.fetchall()
    except Exception as e:
        flash(f'Error loading bookings: {str(e)}', 'error')
    finally:
        conn.close()
    return render_template('my_bookings.html', bookings=bookings)

# ================== USER PROFILE ==================
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('login'))
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT full_name, email FROM users WHERE id = %s", (session['user_id'],))
        user = cursor.fetchone()
    except:
        user = {}
    finally:
        conn.close()
    return render_template('user_profile.html', user=user)

@app.route('/profile/update', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('login'))
    full_name = request.form['full_name']
    email = request.form['email']
    current_password = request.form['current_password']
    new_password = request.form.get('new_password')
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT password FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if user['password'] != current_password:
            flash('Current password is incorrect.', 'error')
            return redirect(url_for('profile'))
        update_query = "UPDATE users SET full_name = %s, email = %s"
        params = [full_name, email]
        if new_password and new_password.strip() != '':
            update_query += ", password = %s"
            params.append(new_password)
        update_query += " WHERE id = %s"
        params.append(user_id)
        cursor.execute(update_query, params)
        conn.commit()
        session['user_name'] = full_name
        flash('Profile updated successfully!', 'success')
    except mysql.connector.IntegrityError:
        flash('Email already in use.', 'error')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    finally:
        conn.close()
    return redirect(url_for('profile'))

# ================== ADMIN DASHBOARD ==================
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('is_admin') != 1:
        flash('Access denied. Admins only.', 'error')
        return redirect(url_for('login'))
    
    search = request.args.get('search', '').strip()
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    all_bookings = []
    total_today = 0
    total_revenue = 0
    popular_room = "N/A"
    try:
        today_str = date_type.today().isoformat()
        cursor.execute("SELECT COUNT(*) AS cnt FROM reservations WHERE date = %s AND status != 'cancelled'", (today_str,))
        total_today = cursor.fetchone()['cnt']
        cursor.execute("""
            SELECT SUM(ro.price) AS revenue
            FROM reservations r
            JOIN rooms ro ON r.room_id = ro.id
            WHERE r.status != 'cancelled'
        """)
        total_revenue = cursor.fetchone()['revenue'] or 0
        cursor.execute("""
            SELECT ro.name, COUNT(*) AS book_count
            FROM reservations r
            JOIN rooms ro ON r.room_id = ro.id
            WHERE r.status != 'cancelled'
            GROUP BY ro.name
            ORDER BY book_count DESC
            LIMIT 1
        """)
        popular = cursor.fetchone()
        if popular:
            popular_room = f"{popular['name']} ({popular['book_count']} bookings)"
        
        if search:
            like_pattern = f"%{search}%"
            cursor.execute("""
                SELECT r.id, r.guest_name, u.email, r.date, r.time_slot, r.status, ro.name AS room_name
                FROM reservations r
                JOIN users u ON r.user_id = u.id
                JOIN rooms ro ON r.room_id = ro.id
                WHERE r.guest_name LIKE %s OR u.email LIKE %s OR r.date LIKE %s OR ro.name LIKE %s
                ORDER BY r.date ASC
            """, (like_pattern, like_pattern, like_pattern, like_pattern))
        else:
            cursor.execute("""
                SELECT r.id, r.guest_name, u.email, r.date, r.time_slot, r.status, ro.name AS room_name
                FROM reservations r
                JOIN users u ON r.user_id = u.id
                JOIN rooms ro ON r.room_id = ro.id
                ORDER BY r.date ASC
            """)
        all_bookings = cursor.fetchall()
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    finally:
        conn.close()
    return render_template('admin_dashboard.html',
                           all_bookings=all_bookings,
                           total_today=total_today,
                           total_revenue=total_revenue,
                           popular_room=popular_room,
                           search=search)

@app.route('/admin/cancel_reservation/<int:reservation_id>', methods=['POST'])
def admin_cancel_reservation(reservation_id):
    if 'user_id' not in session or session.get('is_admin') != 1:
        flash('Access denied.', 'error')
        return redirect(url_for('login'))
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE reservations SET status = 'cancelled' WHERE id = %s", (reservation_id,))
        if cursor.rowcount == 0:
            flash('Reservation not found.', 'error')
        else:
            conn.commit()
            flash('Reservation cancelled.', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    finally:
        conn.close()
    return redirect(url_for('admin_dashboard'))

# ================== ADMIN ROOM MANAGEMENT ==================
# Existing rooms list
@app.route('/admin/existing_rooms')
def admin_existing_rooms():
    if 'user_id' not in session or session.get('is_admin') != 1:
        flash('Access denied.', 'error')
        return redirect(url_for('login'))
    
    search = request.args.get('search_room', '').strip()
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        if search:
            like = f"%{search}%"
            cursor.execute("SELECT * FROM rooms WHERE name LIKE %s OR description LIKE %s ORDER BY name ASC", (like, like))
        else:
            cursor.execute("SELECT * FROM rooms ORDER BY name ASC")
        rooms = cursor.fetchall()
    except Exception as e:
        rooms = []
        flash(f'Error loading rooms: {str(e)}', 'error')
    finally:
        conn.close()
    return render_template('admin_existing_rooms.html', rooms=rooms, search_room=search)

# Add room form page
@app.route('/admin/add_room')
def admin_add_room():
    if 'user_id' not in session or session.get('is_admin') != 1:
        flash('Access denied.', 'error')
        return redirect(url_for('login'))
    return render_template('admin_add_room.html')

# Redirect old /admin/rooms to existing rooms
@app.route('/admin/rooms')
def admin_rooms_redirect():
    return redirect(url_for('admin_existing_rooms'))

# Add room POST
@app.route('/admin/rooms/add', methods=['POST'])
def add_room():
    if 'user_id' not in session or session.get('is_admin') != 1:
        flash('Access denied.', 'error')
        return redirect(url_for('login'))
    name = request.form['name']
    description = request.form.get('description', '')
    price = request.form.get('price', 0)
    capacity = request.form.get('capacity', 1)
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO rooms (name, description, price, capacity) VALUES (%s, %s, %s, %s)",
                       (name, description, price, capacity))
        conn.commit()
        flash('Room added successfully!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    finally:
        conn.close()
    return redirect(url_for('admin_add_room'))

# Edit room POST (update details)
@app.route('/admin/rooms/edit/<int:room_id>', methods=['POST'])
def edit_room(room_id):
    if 'user_id' not in session or session.get('is_admin') != 1:
        flash('Access denied.', 'error')
        return redirect(url_for('login'))
    name = request.form['name']
    description = request.form.get('description', '')
    price = request.form.get('price', 0)
    capacity = request.form.get('capacity', 1)
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE rooms SET name=%s, description=%s, price=%s, capacity=%s WHERE id=%s
        """, (name, description, price, capacity, room_id))
        conn.commit()
        flash('Room updated!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    finally:
        conn.close()
    return redirect(url_for('admin_existing_rooms'))

# Delete room POST
@app.route('/admin/rooms/delete/<int:room_id>', methods=['POST'])
def delete_room(room_id):
    if 'user_id' not in session or session.get('is_admin') != 1:
        flash('Access denied.', 'error')
        return redirect(url_for('login'))
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Delete associated time slots first to avoid foreign key issues
        cursor.execute("DELETE FROM room_time_slots WHERE room_id = %s", (room_id,))
        cursor.execute("DELETE FROM rooms WHERE id = %s", (room_id,))
        conn.commit()
        flash('Room deleted.', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    finally:
        conn.close()
    return redirect(url_for('admin_existing_rooms'))

# Edit room page (view with form and time slots)
@app.route('/admin/rooms/edit/<int:room_id>')
def edit_room_page(room_id):
    if 'user_id' not in session or session.get('is_admin') != 1:
        flash('Access denied.', 'error')
        return redirect(url_for('login'))
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM rooms WHERE id = %s", (room_id,))
        room = cursor.fetchone()
        cursor.execute("SELECT *, time_slot AS slot FROM room_time_slots WHERE room_id = %s ORDER BY time_slot ASC", (room_id,))
        room_slots = cursor.fetchall()
    except Exception as e:
        room = None
        room_slots = []
        flash(f'Error: {str(e)}', 'error')
    finally:
        conn.close()
    if not room:
        flash('Room not found.', 'error')
        return redirect(url_for('admin_existing_rooms'))
    return render_template('edit_room.html', room=room, room_slots=room_slots)

# ================== ADMIN PER-ROOM TIME SLOT MANAGEMENT ==================
@app.route('/admin/room_slot/add/<int:room_id>', methods=['POST'])
def add_room_slot(room_id):
    if 'user_id' not in session or session.get('is_admin') != 1:
        flash('Access denied.', 'error')
        return redirect(url_for('login'))
    slot = request.form['slot'].strip()
    if not slot:
        flash('Slot cannot be empty.', 'error')
        return redirect(url_for('edit_room_page', room_id=room_id))
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO room_time_slots (room_id, time_slot, is_available) VALUES (%s, %s, TRUE)", (room_id, slot))
        conn.commit()
        flash('Time slot added successfully.', 'success')
    except mysql.connector.IntegrityError:
        flash('This time slot already exists for this room.', 'error')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    finally:
        conn.close()
    return redirect(url_for('edit_room_page', room_id=room_id))

@app.route('/admin/room_slot/toggle/<int:slot_id>', methods=['POST'])
def toggle_room_slot(slot_id):
    if 'user_id' not in session or session.get('is_admin') != 1:
        flash('Access denied.', 'error')
        return redirect(url_for('login'))
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE room_time_slots SET is_available = NOT is_available WHERE id = %s", (slot_id,))
        conn.commit()
        flash('Slot availability updated.', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('admin_existing_rooms'))
    finally:
        conn.close()
    conn2 = get_db()
    cursor2 = conn2.cursor(dictionary=True)
    cursor2.execute("SELECT room_id FROM room_time_slots WHERE id = %s", (slot_id,))
    slot = cursor2.fetchone()
    conn2.close()
    if slot:
        return redirect(url_for('edit_room_page', room_id=slot['room_id']))
    else:
        return redirect(url_for('admin_existing_rooms'))

@app.route('/admin/room_slot/delete/<int:slot_id>', methods=['POST'])
def delete_room_slot(slot_id):
    if 'user_id' not in session or session.get('is_admin') != 1:
        flash('Access denied.', 'error')
        return redirect(url_for('login'))
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    room_id = None
    try:
        cursor.execute("SELECT room_id FROM room_time_slots WHERE id = %s", (slot_id,))
        slot = cursor.fetchone()
        if slot:
            room_id = slot['room_id']
            cursor.execute("DELETE FROM room_time_slots WHERE id = %s", (slot_id,))
            conn.commit()
            flash('Time slot deleted.', 'success')
        else:
            flash('Slot not found.', 'error')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    finally:
        conn.close()
    if room_id:
        return redirect(url_for('edit_room_page', room_id=room_id))
    else:
        return redirect(url_for('admin_existing_rooms'))

# ================== ADMIN USER MANAGEMENT ==================
@app.route('/admin/users')
def admin_users():
    if 'user_id' not in session or session.get('is_admin') != 1:
        flash('Access denied.', 'error')
        return redirect(url_for('login'))
    search = request.args.get('search', '').strip()
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        if search:
            like = f"%{search}%"
            cursor.execute("""
                SELECT id, full_name, email, is_admin 
                FROM users 
                WHERE full_name LIKE %s OR email LIKE %s OR 
                      (is_admin = 1 AND 'yes' LIKE %s) OR 
                      (is_admin = 0 AND 'no' LIKE %s)
                ORDER BY id ASC
            """, (like, like, like, like))
        else:
            cursor.execute("SELECT id, full_name, email, is_admin FROM users ORDER BY id ASC")
        users = cursor.fetchall()
    except Exception as e:
        users = []
        flash(f'Error loading users: {str(e)}', 'error')
    finally:
        conn.close()
    return render_template('admin_users.html', users=users, search=search)

# ================== RUN APP ==================
if __name__ == '__main__':
    app.run(debug=True, port=8000)