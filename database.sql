-- Create Database
CREATE DATABASE IF NOT EXISTS user_management;
USE user_management;

-- Create Users Table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL
);

-- Create Grades Table
CREATE TABLE IF NOT EXISTS grades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    subject VARCHAR(100),
    grade CHAR(2),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create Documents Table (For File Uploads)
CREATE TABLE IF NOT EXISTS documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    filename VARCHAR(255) NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

INSERT INTO users (id, username, email, password_hash) 
SELECT 1, 'testuser', 'test@example.com', 'hashed_password' 
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'testuser');

CREATE TABLE uploads(
    id INT AUTO_INCREMENT PRIMARY KEY, 
    user_id INT, filename VARCHAR(255), 
    file_path VARCHAR(255), 
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;
SELECT id, username, email, is_admin FROM users WHERE email = 'your_admin_email@example.com';
UPDATE users SET is_admin = TRUE WHERE email = 'your_admin_email@example.com';
ALTER TABLE users ADD COLUMN grade VARCHAR(5) DEFAULT NULL;
