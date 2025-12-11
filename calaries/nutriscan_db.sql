-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Dec 11, 2025 at 10:18 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.1.25

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `nutriscan_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `food_logs`
--

CREATE TABLE `food_logs` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `date` datetime DEFAULT NULL,
  `food_name` varchar(255) DEFAULT NULL,
  `calories` int(11) DEFAULT NULL,
  `protein` int(11) DEFAULT NULL,
  `carbs` int(11) DEFAULT NULL,
  `fat` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `food_logs`
--

INSERT INTO `food_logs` (`id`, `user_id`, `date`, `food_name`, `calories`, `protein`, `carbs`, `fat`) VALUES
(1, 2, '2025-12-11 05:35:56', 'The image displays a classic grilled cheese sandwich, cut in half diagonally, revealing melted cheese between two slices of golden-brown toasted bread. The nutritional estimation is based on two slices of standard white bread, two slices of American or ch', 500, 20, 40, 35);

-- --------------------------------------------------------

--
-- Table structure for table `site_config`
--

CREATE TABLE `site_config` (
  `id` int(11) NOT NULL,
  `site_name` varchar(100) DEFAULT NULL,
  `support_email` varchar(150) DEFAULT NULL,
  `allow_registrations` tinyint(1) DEFAULT NULL,
  `maintenance_mode` tinyint(1) DEFAULT NULL,
  `default_trial_days` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `site_config`
--

INSERT INTO `site_config` (`id`, `site_name`, `support_email`, `allow_registrations`, `maintenance_mode`, `default_trial_days`) VALUES
(1, 'NutriScan AI', 'support@nutriscan.com', 1, 0, 15);

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `username` varchar(150) NOT NULL,
  `email` varchar(150) NOT NULL,
  `password` varchar(255) NOT NULL,
  `created_at` datetime DEFAULT NULL,
  `is_admin` tinyint(1) DEFAULT NULL,
  `trial_start` datetime DEFAULT NULL,
  `is_premium` tinyint(1) DEFAULT NULL,
  `premium_expiry` datetime DEFAULT NULL,
  `age` int(11) DEFAULT NULL,
  `gender` varchar(10) DEFAULT NULL,
  `current_weight` float DEFAULT NULL,
  `height` float DEFAULT NULL,
  `activity_level` varchar(20) DEFAULT NULL,
  `goal` varchar(50) DEFAULT NULL,
  `daily_calorie_limit` int(11) DEFAULT NULL,
  `saved_diet_plan` text DEFAULT NULL,
  `is_active_account` tinyint(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `username`, `email`, `password`, `created_at`, `is_admin`, `trial_start`, `is_premium`, `premium_expiry`, `age`, `gender`, `current_weight`, `height`, `activity_level`, `goal`, `daily_calorie_limit`, `saved_diet_plan`, `is_active_account`) VALUES
(1, 'Zack Snyder 💥💯', 'admin@nutriscan.com', 'pbkdf2:sha256:1000000$M4Mdi7zGIy8B6WHr$5d44f4487bf4011a715db55bb94ad3fc676a91888a61ffafe946057d742344af', '2025-12-10 13:27:57', 1, '2025-12-10 13:27:57', 0, NULL, NULL, NULL, NULL, NULL, 'sedentary', 'maintain', 2000, NULL, 1),
(2, 'Gokul', 'gokul@gmail.com', 'pbkdf2:sha256:1000000$E8BacdNJP93sjn9o$d2ed9b8fb385cb1c99e155fd6e13b5c2d49baeba60857b96a9315a55a33b8821', '2025-12-10 13:30:01', 0, '2025-12-10 13:30:01', 1, '2026-12-11 06:49:08', 22, 'male', 72, 175, 'sedentary', 'lose', 1550, '<h3>1-Day Weight Loss Diet Plan (Target: 1550 kcal)</h3>\n<ul>\n    <li><h3>Breakfast (Approx. 310 kcal)</h3>\n        <ul>\n            <li>1/2 cup (dry) Rolled Oats cooked with water</li>\n            <li>1 scoop Whey Protein Powder (mixed with oats or water)</li>\n            <li>1/2 cup Mixed Berries (e.g., blueberries, raspberries)</li>\n        </ul>\n    </li>\n    <li><h3>Lunch (Approx. 475 kcal)</h3>\n        <ul>\n            <li>4 oz (120g) Cooked Chicken Breast (baked or grilled)</li>\n            <li>Large mixed greens salad (spinach, lettuce, cucumber)</li>\n            <li>1 tbsp Light Vinaigrette Dressing</li>\n            <li>1/2 cup Cooked Quinoa or Brown Rice</li>\n            <li>1 cup Steamed or Roasted Mixed Vegetables (e.g., broccoli, bell peppers)</li>\n            <li>1/4 medium Avocado</li>\n        </ul>\n    </li>\n    <li><h3>Snack 1 (Approx. 180 kcal)</h3>\n        <ul>\n            <li>150g Plain Non-Fat Greek Yogurt</li>\n            <li>1 medium Apple</li>\n        </ul>\n    </li>\n    <li><h3>Dinner (Approx. 450 kcal)</h3>\n        <ul>\n            <li>4 oz (120g) Baked Salmon Fillet</li>\n            <li>1 medium Sweet Potato (approx. 150g), baked or roasted</li>\n            <li>1 cup Steamed Asparagus</li>\n            <li>1 tsp Olive Oil (drizzled over salmon/veg)</li>\n        </ul>\n    </li>\n    <li><h3>Snack 2 (Approx. 130 kcal)</h3>\n        <ul>\n            <li>1/2 cup Low-Fat Cottage Cheese</li>\n            <li>1 cup Baby Carrots</li>\n        </ul>\n    </li>\n</ul>', 1),
(3, 'RAGAV', 'Ragavarshini@gmail.com', 'pbkdf2:sha256:1000000$VM7OqMaXKNIKxXaz$66ab778937fde26de2e7efc6eb38c5d1d9dfbb939331ba031bd9b96d796804e2', '2025-12-11 07:17:28', 0, '2025-12-11 07:17:28', 0, NULL, NULL, NULL, NULL, NULL, 'sedentary', 'maintain', 2000, NULL, 1);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `food_logs`
--
ALTER TABLE `food_logs`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `site_config`
--
ALTER TABLE `site_config`
  ADD PRIMARY KEY (`id`);

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
-- AUTO_INCREMENT for table `food_logs`
--
ALTER TABLE `food_logs`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `site_config`
--
ALTER TABLE `site_config`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `food_logs`
--
ALTER TABLE `food_logs`
  ADD CONSTRAINT `food_logs_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
