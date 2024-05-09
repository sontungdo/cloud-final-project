#!/bin/bash

apt-get update -y
apt-get upgrade -y
apt-get install -y wget
apt-get install -y python3-pip
pip3 install --upgrade flask
pip3 install --upgrade mysql-connector-python
pip3 install --upgrade python-dateutil

# Install MySQL
apt-get install -y mysql-server

# Configure MySQL
mysql -u root <<EOF
CREATE DATABASE todolist;
USE todolist;

CREATE TABLE entries (
  id INT AUTO_INCREMENT PRIMARY KEY,
  what_to_do VARCHAR(255) NOT NULL,
  due_date DATE,
  status VARCHAR(255) DEFAULT 'not done',
  recurring_interval VARCHAR(20),
  user_id INT,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL
);
EOF

# download the code
wget https://github.com/sontungdo/cloud-final-project/blob/main/todolist_api.py

python3 todolist_api.py
