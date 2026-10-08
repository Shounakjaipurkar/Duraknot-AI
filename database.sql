-- DuraKnot Production Monitoring & AI Inspection Database
-- Based on the tables and fields used by the Flask backend.

CREATE DATABASE IF NOT EXISTS duraknot_production;
USE duraknot_production;

-- -----------------------------------------------------
-- USERS
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    name VARCHAR(150) NOT NULL
);

-- -----------------------------------------------------
-- LOGIN HISTORY
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS login_history (
    login_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    username VARCHAR(100) NOT NULL,
    login_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    logout_time DATETIME NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- -----------------------------------------------------
-- PRODUCTION ROLLS
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS production_rolls (
    roll_id INT AUTO_INCREMENT PRIMARY KEY,
    roll_number VARCHAR(50) NOT NULL UNIQUE,
    required_length DECIMAL(10,2) NOT NULL,
    current_length DECIMAL(10,2) NOT NULL DEFAULT 0,
    status ENUM('RUNNING', 'COMPLETED') NOT NULL DEFAULT 'RUNNING',
    start_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_time DATETIME NULL
);

-- -----------------------------------------------------
-- AI DETECTIONS
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS ai_detections (
    detection_id INT AUTO_INCREMENT PRIMARY KEY,
    roll_id INT NOT NULL,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    defect_type VARCHAR(100) NOT NULL,
    confidence DECIMAL(6,2) NOT NULL,
    x1 INT NULL,
    y1 INT NULL,
    x2 INT NULL,
    y2 INT NULL,
    image_saved VARCHAR(500) NULL,
    FOREIGN KEY (roll_id) REFERENCES production_rolls(roll_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- -----------------------------------------------------
-- ALERTS
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS alerts (
    alert_id INT AUTO_INCREMENT PRIMARY KEY,
    alert_type VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE'
);

-- -----------------------------------------------------
-- SAMPLE USER
-- Change/remove this before using the database publicly.
-- -----------------------------------------------------
INSERT INTO users (username, password, name)
VALUES ('admin', 'change_this_password', 'Administrator')
ON DUPLICATE KEY UPDATE username = username;

-- -----------------------------------------------------
-- INITIAL PRODUCTION ROLL
-- -----------------------------------------------------
INSERT INTO production_rolls
    (roll_number, required_length, current_length, status, start_time)
SELECT
    'DRK-0001', 1000.00, 0.00, 'RUNNING', NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM production_rolls
);

-- -----------------------------------------------------
-- Useful indexes
-- -----------------------------------------------------
CREATE INDEX idx_production_status
    ON production_rolls(status);

CREATE INDEX idx_detection_roll
    ON ai_detections(roll_id);

CREATE INDEX idx_detection_timestamp
    ON ai_detections(timestamp);

CREATE INDEX idx_alert_created
    ON alerts(created_at);
