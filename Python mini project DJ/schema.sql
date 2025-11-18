-- schema.sql
CREATE DATABASE IF NOT EXISTS inventory_app;
USE inventory_app;

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(20) DEFAULT 'admin'
);

CREATE TABLE IF NOT EXISTS suppliers (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  contact VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS products (
  id INT AUTO_INCREMENT PRIMARY KEY,
  sku VARCHAR(50) UNIQUE NOT NULL,
  name VARCHAR(150) NOT NULL,
  cost DECIMAL(10,2) DEFAULT 0,
  price DECIMAL(10,2) DEFAULT 0,
  stock INT DEFAULT 0,
  reorder_point INT DEFAULT 10,
  lead_time_days INT DEFAULT 7,
  supplier_id INT,
  FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
);

CREATE TABLE IF NOT EXISTS sales (
  id INT AUTO_INCREMENT PRIMARY KEY,
  product_id INT,
  sale_date DATE,
  quantity INT,
  customer VARCHAR(150),
  FOREIGN KEY (product_id) REFERENCES products(id)
);

-- seed admin (demo only)
INSERT IGNORE INTO users (username, password_hash, role) VALUES ('admin', 'admin', 'admin');
