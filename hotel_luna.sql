-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: May 29, 2026 at 02:39 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `hotel_luna`
--

-- --------------------------------------------------------

--
-- Table structure for table `reservations`
--

CREATE TABLE `reservations` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `room_id` int(11) NOT NULL,
  `guest_name` varchar(100) NOT NULL,
  `date` date NOT NULL,
  `time_slot` varchar(50) NOT NULL,
  `status` varchar(20) DEFAULT 'confirmed'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `reservations`
--

INSERT INTO `reservations` (`id`, `user_id`, `room_id`, `guest_name`, `date`, `time_slot`, `status`) VALUES
(1, 1, 1, 'Zeth Ramzy Pagcaliwagan', '2026-05-23', '09:00-10:00', 'cancelled'),
(2, 6, 1, 'Juan Dela Cruz', '2026-05-23', '09:00-12:00', 'confirmed');

-- --------------------------------------------------------

--
-- Table structure for table `rooms`
--

CREATE TABLE `rooms` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `price` decimal(10,2) DEFAULT 0.00,
  `capacity` int(11) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `rooms`
--

INSERT INTO `rooms` (`id`, `name`, `description`, `price`, `capacity`) VALUES
(1, 'Deluxe Room', 'This is the deluxe room', 700.00, 2),
(3, 'Deluxe Room', 'Spacious room with king-size bed, city view, and mini-bar.', 2500.00, 2),
(4, 'Family Suite', 'Two connecting bedrooms, living area, and kitchenette. Perfect for families.', 4000.00, 4),
(5, 'Executive Suite', 'Luxury suite with separate office area, jacuzzi, and free breakfast.', 5500.00, 2),
(6, 'Presidential Suite', 'Penthouse level with panoramic view, private butler service, and premium amenities.', 12000.00, 4),
(7, 'Single Economy', 'Small but comfortable room for solo travelers, with basic amenities.', 900.00, 1),
(8, 'Ocean View Room', 'Room with balcony overlooking the sea. Includes lounge chairs.', 3200.00, 2),
(9, 'Honeymoon Suite', 'Romantic setup with heart-shaped bed, flower decoration, and champagne.', 7000.00, 2),
(10, 'Single Room', 'Single Minimalist Room', 500.00, 1);

-- --------------------------------------------------------

--
-- Table structure for table `room_time_slots`
--

CREATE TABLE `room_time_slots` (
  `id` int(11) NOT NULL,
  `room_id` int(11) NOT NULL,
  `time_slot` varchar(50) NOT NULL,
  `is_available` tinyint(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `room_time_slots`
--

INSERT INTO `room_time_slots` (`id`, `room_id`, `time_slot`, `is_available`) VALUES
(1, 1, '09:00-12:00', 1),
(2, 1, '09:00-10:00', 1);

-- --------------------------------------------------------

--
-- Table structure for table `time_slots`
--

CREATE TABLE `time_slots` (
  `id` int(11) NOT NULL,
  `slot` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `time_slots`
--

INSERT INTO `time_slots` (`id`, `slot`) VALUES
(8, '07:00-08:00'),
(9, '08:00-09:00'),
(1, '09:00-10:00'),
(7, '09:00-12:00'),
(2, '10:00-11:00'),
(3, '11:00-12:00'),
(10, '12:00-13:00'),
(4, '13:00-14:00'),
(5, '14:00-15:00'),
(6, '15:00-16:00'),
(11, '16:00-17:00'),
(12, '17:00-18:00'),
(13, '18:00-19:00'),
(14, '19:00-20:00');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `full_name` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `is_admin` tinyint(1) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `full_name`, `email`, `password`, `is_admin`) VALUES
(1, 'Zeth Ramzy Pagcaliwagan', 'pagcaliwaganramzy@gmail.com', '12345678', 0),
(2, 'Admin Luna', 'admin@hotelluna.com', 'admin123', 1),
(3, 'Camilla Misal', 'camilla@gmail.com', '12345678', 0),
(5, 'Camilla Misal', 'Camillamisal@gmail.com', '0987654321', 0),
(6, 'Juan Dela Cruz', 'delacruz@gmail.com', '1234567', 0);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `reservations`
--
ALTER TABLE `reservations`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `room_id` (`room_id`);

--
-- Indexes for table `rooms`
--
ALTER TABLE `rooms`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `room_time_slots`
--
ALTER TABLE `room_time_slots`
  ADD PRIMARY KEY (`id`),
  ADD KEY `room_id` (`room_id`);

--
-- Indexes for table `time_slots`
--
ALTER TABLE `time_slots`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `slot` (`slot`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `reservations`
--
ALTER TABLE `reservations`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `rooms`
--
ALTER TABLE `rooms`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `room_time_slots`
--
ALTER TABLE `room_time_slots`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `time_slots`
--
ALTER TABLE `time_slots`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=15;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `reservations`
--
ALTER TABLE `reservations`
  ADD CONSTRAINT `reservations_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `reservations_ibfk_2` FOREIGN KEY (`room_id`) REFERENCES `rooms` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `room_time_slots`
--
ALTER TABLE `room_time_slots`
  ADD CONSTRAINT `room_time_slots_ibfk_1` FOREIGN KEY (`room_id`) REFERENCES `rooms` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
