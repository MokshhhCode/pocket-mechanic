-- ========================================================================
-- POCKET MECHANIC: MASTER OFF-LINE MYSQL DATABASE SCHEMA
-- Stage 1: Software-Only Predictive Motorcycle Diagnostics Platform
-- Normalized 28-Entity Relational Model
-- ========================================================================

CREATE DATABASE IF NOT EXISTS `pocket_mechanic_db`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `pocket_mechanic_db`;

SET FOREIGN_KEY_CHECKS = 0;

-- 1. Users table (Personal info with encrypted licence at rest)
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `user_id` INT AUTO_INCREMENT PRIMARY KEY,
  `full_name` VARCHAR(120) NOT NULL,
  `email` VARCHAR(150) NOT NULL UNIQUE,
  `city` VARCHAR(80) NOT NULL,
  `state` VARCHAR(80) NOT NULL,
  `encrypted_licence` TEXT NOT NULL,
  `licence_last4` VARCHAR(8) NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_users_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. User Credentials table
DROP TABLE IF EXISTS `user_credentials`;
CREATE TABLE `user_credentials` (
  `credential_id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL UNIQUE,
  `password_hash` VARCHAR(255) NOT NULL,
  `last_login_at` TIMESTAMP NULL DEFAULT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Manufacturers table (28 Verified OEMs)
DROP TABLE IF EXISTS `manufacturers`;
CREATE TABLE `manufacturers` (
  `manufacturer_id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(80) NOT NULL UNIQUE,
  `country` VARCHAR(60) NOT NULL,
  `founded_year` INT NULL,
  `logo_slug` VARCHAR(80) NOT NULL,
  `is_active` BOOLEAN DEFAULT TRUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Motorcycle Models table
DROP TABLE IF EXISTS `motorcycle_models`;
CREATE TABLE `motorcycle_models` (
  `model_id` INT AUTO_INCREMENT PRIMARY KEY,
  `manufacturer_id` INT NOT NULL,
  `name` VARCHAR(100) NOT NULL,
  `category` VARCHAR(50) NOT NULL, -- Cruiser, Naked, Sport, Adventure, Commuter
  `image_url` VARCHAR(255) NULL,
  `silhouette_code` VARCHAR(50) DEFAULT 'default_standard',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`manufacturer_id`) REFERENCES `manufacturers` (`manufacturer_id`) ON DELETE CASCADE,
  INDEX `idx_models_mfg` (`manufacturer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Motorcycle Variants table
DROP TABLE IF EXISTS `motorcycle_variants`;
CREATE TABLE `motorcycle_variants` (
  `variant_id` INT AUTO_INCREMENT PRIMARY KEY,
  `model_id` INT NOT NULL,
  `variant_name` VARCHAR(100) NOT NULL,
  `year_start` INT NOT NULL,
  `year_end` INT NULL,
  `cooling_type` VARCHAR(60) NOT NULL DEFAULT 'Air',
  `brake_type` VARCHAR(60) NOT NULL DEFAULT 'Dual Disc',
  `abs_type` VARCHAR(60) NOT NULL DEFAULT 'Dual Channel',
  `final_drive_type` VARCHAR(60) NOT NULL DEFAULT 'Chain',
  `fuel_delivery_type` VARCHAR(60) NOT NULL DEFAULT 'Fuel Injection',
  `wheel_type` VARCHAR(60) NOT NULL DEFAULT 'Alloy',
  FOREIGN KEY (`model_id`) REFERENCES `motorcycle_models` (`model_id`) ON DELETE CASCADE,
  INDEX `idx_var_model` (`model_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Motorcycle Technical Specifications table
DROP TABLE IF EXISTS `motorcycle_specifications`;
CREATE TABLE `motorcycle_specifications` (
  `spec_id` INT AUTO_INCREMENT PRIMARY KEY,
  `variant_id` INT NOT NULL UNIQUE,
  `engine_config` VARCHAR(150) NULL,
  `displacement_cc` DECIMAL(7,1) NOT NULL,
  `num_cylinders` INT NOT NULL DEFAULT 1,
  `bore_mm` DECIMAL(5,2) NULL,
  `stroke_mm` DECIMAL(5,2) NULL,
  `compression_ratio` VARCHAR(40) NULL,
  `max_power_bhp` DECIMAL(6,2) NULL,
  `max_power_rpm` INT NULL,
  `max_torque_nm` DECIMAL(6,2) NULL,
  `max_torque_rpm` INT NULL,
  `lubrication_system` VARCHAR(100) NULL,
  `oil_capacity_l` DECIMAL(4,2) NULL,
  `oil_grade` VARCHAR(80) NULL,
  `oil_filter_type` VARCHAR(80) NULL,
  `spark_plug_type` VARCHAR(100) NULL,
  `spark_plug_gap_mm` DECIMAL(4,2) NULL,
  `valve_config` VARCHAR(100) NULL,
  `intake_valve_clearance_mm` VARCHAR(80) NULL,
  `exhaust_valve_clearance_mm` VARCHAR(80) NULL,
  `idle_rpm` INT DEFAULT 1200,
  `num_gears` INT NOT NULL DEFAULT 5,
  `gearbox_type` VARCHAR(100) DEFAULT 'Manual',
  `clutch_type` VARCHAR(100) DEFAULT 'Wet Multi-plate',
  `chain_slack_mm` VARCHAR(80) NULL,
  `front_brake_type` VARCHAR(150) NULL,
  `rear_brake_type` VARCHAR(150) NULL,
  `front_disc_dia_mm` INT NULL,
  `rear_disc_dia_mm` INT NULL,
  `brake_fluid_type` VARCHAR(60) DEFAULT 'DOT 4',
  `brake_fluid_interval_km` INT DEFAULT 20000,
  `front_suspension` VARCHAR(150) NULL,
  `rear_suspension` VARCHAR(150) NULL,
  `suspension_travel_front_mm` INT NULL,
  `suspension_travel_rear_mm` INT NULL,
  `frame_type` VARCHAR(150) NULL,
  `front_tyre_size` VARCHAR(80) NULL,
  `rear_tyre_size` VARCHAR(80) NULL,
  `tyre_type` VARCHAR(80) DEFAULT 'Tubeless',
  `front_tyre_psi` INT DEFAULT 29,
  `rear_tyre_psi` INT DEFAULT 33,
  `battery_voltage` DECIMAL(4,1) DEFAULT 12.0,
  `battery_capacity_ah` DECIMAL(4,1) DEFAULT 8.0,
  `battery_type` VARCHAR(80) DEFAULT 'Maintenance Free VRLA',
  `charging_system` VARCHAR(100) DEFAULT 'Alternator & Regulator/Rectifier',
  `fuel_tank_capacity_l` DECIMAL(5,1) NULL,
  `coolant_capacity_l` DECIMAL(4,2) NULL,
  `coolant_spec` VARCHAR(100) NULL,
  `kerb_weight_kg` DECIMAL(6,1) NULL,
  `service_interval_km` INT DEFAULT 5000,
  `service_interval_months` INT DEFAULT 6,
  FOREIGN KEY (`variant_id`) REFERENCES `motorcycle_variants` (`variant_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. Specification Sources table
DROP TABLE IF EXISTS `specification_sources`;
CREATE TABLE `specification_sources` (
  `source_id` INT AUTO_INCREMENT PRIMARY KEY,
  `spec_id` INT NOT NULL,
  `source_name` VARCHAR(120) NOT NULL,
  `source_url` VARCHAR(255) NULL,
  `source_date` VARCHAR(30) NULL,
  `document_type` VARCHAR(60) NOT NULL, -- Owner Manual, Workshop Manual, OEM Spec Sheet
  `verification_status` ENUM('Verified', 'Preliminary', 'Unverified') DEFAULT 'Verified',
  FOREIGN KEY (`spec_id`) REFERENCES `motorcycle_specifications` (`spec_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. User Registered Motorcycles table
DROP TABLE IF EXISTS `motorcycles`;
CREATE TABLE `motorcycles` (
  `motorcycle_id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `variant_id` INT NULL,
  `custom_make` VARCHAR(80) NULL,
  `custom_model` VARCHAR(100) NULL,
  `manufacturing_year` INT NOT NULL,
  `colour` VARCHAR(50) NOT NULL,
  `registration_number` VARCHAR(30) NOT NULL,
  `current_odometer_km` INT DEFAULT 5000,
  `is_active` BOOLEAN DEFAULT TRUE,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  FOREIGN KEY (`variant_id`) REFERENCES `motorcycle_variants` (`variant_id`) ON DELETE SET NULL,
  INDEX `idx_user_bikes` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. Component Catalogue table
DROP TABLE IF EXISTS `component_catalogue`;
CREATE TABLE `component_catalogue` (
  `component_id` INT AUTO_INCREMENT PRIMARY KEY,
  `component_code` VARCHAR(50) NOT NULL UNIQUE,
  `name` VARCHAR(80) NOT NULL,
  `category` ENUM('Powertrain', 'Chassis', 'Braking', 'Electrical', 'Fluids', 'Tyres') NOT NULL,
  `description` TEXT NULL,
  `is_critical` BOOLEAN DEFAULT FALSE,
  `check_interval_group` ENUM('Every Ride', 'Weekly', 'Periodic') NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 10. Model Component Applicability table
DROP TABLE IF EXISTS `model_component_applicability`;
CREATE TABLE `model_component_applicability` (
  `applicability_id` INT AUTO_INCREMENT PRIMARY KEY,
  `variant_id` INT NOT NULL,
  `component_id` INT NOT NULL,
  `is_applicable` BOOLEAN DEFAULT TRUE,
  `rule_condition` VARCHAR(120) NULL,
  `display_name_override` VARCHAR(80) NULL,
  `notes` VARCHAR(255) NULL,
  FOREIGN KEY (`variant_id`) REFERENCES `motorcycle_variants` (`variant_id`) ON DELETE CASCADE,
  FOREIGN KEY (`component_id`) REFERENCES `component_catalogue` (`component_id`) ON DELETE CASCADE,
  UNIQUE KEY `uk_var_comp` (`variant_id`, `component_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 11. Maintenance Schedules table
DROP TABLE IF EXISTS `maintenance_schedules`;
CREATE TABLE `maintenance_schedules` (
  `schedule_id` INT AUTO_INCREMENT PRIMARY KEY,
  `variant_id` INT NOT NULL,
  `component_id` INT NOT NULL,
  `schedule_group` ENUM('Every Ride', 'Weekly', 'Periodic') NOT NULL,
  `interval_km` INT NULL,
  `interval_days` INT NULL,
  `inspection_action` VARCHAR(255) NOT NULL,
  `replacement_action` VARCHAR(255) NULL,
  `is_mandatory` BOOLEAN DEFAULT TRUE,
  FOREIGN KEY (`variant_id`) REFERENCES `motorcycle_variants` (`variant_id`) ON DELETE CASCADE,
  FOREIGN KEY (`component_id`) REFERENCES `component_catalogue` (`component_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 12. Sensor Definitions table
DROP TABLE IF EXISTS `sensor_definitions`;
CREATE TABLE `sensor_definitions` (
  `sensor_id` INT AUTO_INCREMENT PRIMARY KEY,
  `sensor_code` VARCHAR(50) NOT NULL UNIQUE,
  `name` VARCHAR(80) NOT NULL,
  `category` VARCHAR(50) NOT NULL,
  `unit` VARCHAR(20) NOT NULL,
  `min_normal` DECIMAL(8,2) NOT NULL,
  `max_normal` DECIMAL(8,2) NOT NULL,
  `min_critical` DECIMAL(8,2) NOT NULL,
  `max_critical` DECIMAL(8,2) NOT NULL,
  `sampling_frequency_hz` DECIMAL(5,2) DEFAULT 1.0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 13. Sensor Configurations table
DROP TABLE IF EXISTS `sensor_configurations`;
CREATE TABLE `sensor_configurations` (
  `config_id` INT AUTO_INCREMENT PRIMARY KEY,
  `variant_id` INT NOT NULL,
  `sensor_id` INT NOT NULL,
  `is_installed` BOOLEAN DEFAULT TRUE,
  `is_simulated` BOOLEAN DEFAULT TRUE,
  `calibration_offset` DECIMAL(6,2) DEFAULT 0.00,
  `alert_threshold_low` DECIMAL(8,2) NULL,
  `alert_threshold_high` DECIMAL(8,2) NULL,
  FOREIGN KEY (`variant_id`) REFERENCES `motorcycle_variants` (`variant_id`) ON DELETE CASCADE,
  FOREIGN KEY (`sensor_id`) REFERENCES `sensor_definitions` (`sensor_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 14. Sensor Readings table (Simulated & Hardware Telemetry with source tag)
DROP TABLE IF EXISTS `sensor_readings`;
CREATE TABLE `sensor_readings` (
  `reading_id` BIGINT AUTO_INCREMENT PRIMARY KEY,
  `motorcycle_id` INT NOT NULL,
  `sensor_id` INT NOT NULL,
  `timestamp` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `value` DECIMAL(10,3) NOT NULL,
  `source_type` ENUM('SIMULATED', 'HARDWARE') NOT NULL DEFAULT 'SIMULATED',
  `is_anomaly` BOOLEAN DEFAULT FALSE,
  `session_id` VARCHAR(64) NULL,
  FOREIGN KEY (`motorcycle_id`) REFERENCES `motorcycles` (`motorcycle_id`) ON DELETE CASCADE,
  FOREIGN KEY (`sensor_id`) REFERENCES `sensor_definitions` (`sensor_id`) ON DELETE CASCADE,
  INDEX `idx_readings_bike_time` (`motorcycle_id`, `timestamp`),
  INDEX `idx_readings_sensor` (`sensor_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 15. Simulation Sessions table
DROP TABLE IF EXISTS `simulation_sessions`;
CREATE TABLE `simulation_sessions` (
  `session_id` VARCHAR(64) PRIMARY KEY,
  `motorcycle_id` INT NOT NULL,
  `intensity_level` ENUM('Regular', 'Medium', 'Intense') NOT NULL DEFAULT 'Regular',
  `start_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `end_time` TIMESTAMP NULL DEFAULT NULL,
  `fault_profile` VARCHAR(100) DEFAULT 'Nominal',
  `total_readings` INT DEFAULT 0,
  `status` ENUM('ACTIVE', 'COMPLETED', 'TERMINATED') DEFAULT 'ACTIVE',
  FOREIGN KEY (`motorcycle_id`) REFERENCES `motorcycles` (`motorcycle_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 16. Diagnostic Sessions table
DROP TABLE IF EXISTS `diagnostic_sessions`;
CREATE TABLE `diagnostic_sessions` (
  `session_id` VARCHAR(64) PRIMARY KEY,
  `motorcycle_id` INT NOT NULL,
  `user_id` INT NOT NULL,
  `component_id` INT NULL,
  `trigger_source` ENUM('USER_MANUAL', 'WRENCHY_AI', 'TELEMETRY_ALERT') DEFAULT 'USER_MANUAL',
  `status` ENUM('INITIALIZING', 'PROCESSING', 'COMPLETED', 'FAILED') DEFAULT 'INITIALIZING',
  `started_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `completed_at` TIMESTAMP NULL DEFAULT NULL,
  FOREIGN KEY (`motorcycle_id`) REFERENCES `motorcycles` (`motorcycle_id`) ON DELETE CASCADE,
  FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  FOREIGN KEY (`component_id`) REFERENCES `component_catalogue` (`component_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 17. Diagnostic Tickets table
DROP TABLE IF EXISTS `diagnostic_tickets`;
CREATE TABLE `diagnostic_tickets` (
  `ticket_id` INT AUTO_INCREMENT PRIMARY KEY,
  `motorcycle_id` INT NOT NULL,
  `user_id` INT NOT NULL,
  `component_id` INT NULL,
  `issue_title` VARCHAR(150) NOT NULL,
  `severity` ENUM('Low', 'Medium', 'High', 'Critical') NOT NULL DEFAULT 'Medium',
  `status` ENUM('Open', 'Under Investigation', 'Awaiting Maintenance', 'Resolved', 'Reopened') NOT NULL DEFAULT 'Open',
  `description` TEXT NOT NULL,
  `recommended_action` TEXT NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `resolved_at` TIMESTAMP NULL DEFAULT NULL,
  FOREIGN KEY (`motorcycle_id`) REFERENCES `motorcycles` (`motorcycle_id`) ON DELETE CASCADE,
  FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  FOREIGN KEY (`component_id`) REFERENCES `component_catalogue` (`component_id`) ON DELETE SET NULL,
  INDEX `idx_tickets_user_status` (`user_id`, `status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 18. Diagnostic Results table
DROP TABLE IF EXISTS `diagnostic_results`;
CREATE TABLE `diagnostic_results` (
  `result_id` INT AUTO_INCREMENT PRIMARY KEY,
  `ticket_id` INT NOT NULL,
  `session_id` VARCHAR(64) NULL,
  `model_name` VARCHAR(80) NOT NULL,
  `predicted_condition` ENUM('Normal', 'Attention Required', 'Urgent Attention Required') NOT NULL,
  `confidence_score` DECIMAL(5,4) NOT NULL,
  `anomaly_detected` BOOLEAN DEFAULT FALSE,
  `raw_features_json` JSON NOT NULL,
  `live_trace_json` JSON NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`ticket_id`) REFERENCES `diagnostic_tickets` (`ticket_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 19. Maintenance Records table
DROP TABLE IF EXISTS `maintenance_records`;
CREATE TABLE `maintenance_records` (
  `record_id` INT AUTO_INCREMENT PRIMARY KEY,
  `motorcycle_id` INT NOT NULL,
  `ticket_id` INT NULL,
  `service_date` DATE NOT NULL,
  `odometer_reading_km` INT NOT NULL,
  `service_type` VARCHAR(80) NOT NULL,
  `description` TEXT NOT NULL,
  `service_center` VARCHAR(120) NULL,
  `total_cost` DECIMAL(10,2) DEFAULT 0.00,
  `performed_by` VARCHAR(80) NULL,
  `notes` TEXT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`motorcycle_id`) REFERENCES `motorcycles` (`motorcycle_id`) ON DELETE CASCADE,
  FOREIGN KEY (`ticket_id`) REFERENCES `diagnostic_tickets` (`ticket_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 20. Component Replacements table
DROP TABLE IF EXISTS `component_replacements`;
CREATE TABLE `component_replacements` (
  `replacement_id` INT AUTO_INCREMENT PRIMARY KEY,
  `record_id` INT NOT NULL,
  `motorcycle_id` INT NOT NULL,
  `component_id` INT NOT NULL,
  `part_name` VARCHAR(100) NOT NULL,
  `part_number` VARCHAR(60) NULL,
  `replaced_at_odometer_km` INT NOT NULL,
  `cost` DECIMAL(10,2) DEFAULT 0.00,
  `warranty_months` INT DEFAULT 6,
  `replaced_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`record_id`) REFERENCES `maintenance_records` (`record_id`) ON DELETE CASCADE,
  FOREIGN KEY (`motorcycle_id`) REFERENCES `motorcycles` (`motorcycle_id`) ON DELETE CASCADE,
  FOREIGN KEY (`component_id`) REFERENCES `component_catalogue` (`component_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 21. ML Models Registry table
DROP TABLE IF EXISTS `ml_models`;
CREATE TABLE `ml_models` (
  `model_id` INT AUTO_INCREMENT PRIMARY KEY,
  `model_name` VARCHAR(80) NOT NULL UNIQUE,
  `model_type` ENUM('Classification', 'Regression', 'Clustering', 'Dimensionality Reduction') NOT NULL,
  `algorithm` VARCHAR(60) NOT NULL,
  `version` VARCHAR(20) NOT NULL DEFAULT 'v1.0.0',
  `filepath` VARCHAR(255) NOT NULL,
  `is_active` BOOLEAN DEFAULT TRUE,
  `target_component` VARCHAR(60) NOT NULL,
  `trained_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 22. ML Training Runs table
DROP TABLE IF EXISTS `ml_training_runs`;
CREATE TABLE `ml_training_runs` (
  `run_id` INT AUTO_INCREMENT PRIMARY KEY,
  `model_id` INT NOT NULL,
  `dataset_name` VARCHAR(100) NOT NULL,
  `sample_count` INT NOT NULL,
  `feature_columns_json` JSON NOT NULL,
  `hyperparameters_json` JSON NOT NULL,
  `training_duration_sec` DECIMAL(6,2) NOT NULL,
  `completed_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`model_id`) REFERENCES `ml_models` (`model_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 23. ML Predictions Log table
DROP TABLE IF EXISTS `ml_predictions`;
CREATE TABLE `ml_predictions` (
  `prediction_id` BIGINT AUTO_INCREMENT PRIMARY KEY,
  `model_id` INT NOT NULL,
  `motorcycle_id` INT NOT NULL,
  `input_features_json` JSON NOT NULL,
  `predicted_class` VARCHAR(60) NULL,
  `probability` DECIMAL(5,4) NULL,
  `regression_value` DECIMAL(10,3) NULL,
  `timestamp` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`model_id`) REFERENCES `ml_models` (`model_id`) ON DELETE CASCADE,
  FOREIGN KEY (`motorcycle_id`) REFERENCES `motorcycles` (`motorcycle_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 24. ML Evaluation Metrics table
DROP TABLE IF EXISTS `ml_evaluation_metrics`;
CREATE TABLE `ml_evaluation_metrics` (
  `metric_id` INT AUTO_INCREMENT PRIMARY KEY,
  `run_id` INT NOT NULL,
  `accuracy` DECIMAL(5,4) NULL,
  `precision_score` DECIMAL(5,4) NULL,
  `recall` DECIMAL(5,4) NULL,
  `f1_score` DECIMAL(5,4) NULL,
  `roc_auc` DECIMAL(5,4) NULL,
  `mae` DECIMAL(8,4) NULL,
  `rmse` DECIMAL(8,4) NULL,
  `r2_score` DECIMAL(5,4) NULL,
  `confusion_matrix_json` JSON NULL,
  FOREIGN KEY (`run_id`) REFERENCES `ml_training_runs` (`run_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 25. Chatbot Conversations table (Wrenchy AI)
DROP TABLE IF EXISTS `chatbot_conversations`;
CREATE TABLE `chatbot_conversations` (
  `conversation_id` VARCHAR(64) PRIMARY KEY,
  `user_id` INT NOT NULL,
  `motorcycle_id` INT NOT NULL,
  `title` VARCHAR(150) NOT NULL DEFAULT 'Diagnostic Chat',
  `active_ticket_id` INT NULL,
  `started_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `last_message_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  FOREIGN KEY (`motorcycle_id`) REFERENCES `motorcycles` (`motorcycle_id`) ON DELETE CASCADE,
  FOREIGN KEY (`active_ticket_id`) REFERENCES `diagnostic_tickets` (`ticket_id`) ON DELETE SET NULL,
  INDEX `idx_conv_user_bike` (`user_id`, `motorcycle_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 26. Chatbot Messages table
DROP TABLE IF EXISTS `chatbot_messages`;
CREATE TABLE `chatbot_messages` (
  `message_id` INT AUTO_INCREMENT PRIMARY KEY,
  `conversation_id` VARCHAR(64) NOT NULL,
  `sender` ENUM('USER', 'WRENCHY', 'SYSTEM') NOT NULL,
  `message_text` TEXT NOT NULL,
  `payload_json` JSON NULL,
  `tokens_used` INT DEFAULT 0,
  `timestamp` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`conversation_id`) REFERENCES `chatbot_conversations` (`conversation_id`) ON DELETE CASCADE,
  INDEX `idx_messages_conv` (`conversation_id`, `timestamp`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 27. Application Settings table (Dev Toolbar, Theme, Modes)
DROP TABLE IF EXISTS `application_settings`;
CREATE TABLE `application_settings` (
  `setting_id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NULL,
  `setting_key` VARCHAR(60) NOT NULL,
  `setting_value` VARCHAR(255) NOT NULL,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY `uk_user_setting` (`user_id`, `setting_key`),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 28. Audit Logs table (Security & Ticket Status Tracking)
DROP TABLE IF EXISTS `audit_logs`;
CREATE TABLE `audit_logs` (
  `log_id` BIGINT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NULL,
  `action` VARCHAR(80) NOT NULL,
  `entity_type` VARCHAR(60) NOT NULL,
  `entity_id` VARCHAR(64) NOT NULL,
  `details_json` JSON NULL,
  `ip_address` VARCHAR(45) DEFAULT '127.0.0.1',
  `timestamp` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE SET NULL,
  INDEX `idx_audit_user` (`user_id`, `timestamp`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
