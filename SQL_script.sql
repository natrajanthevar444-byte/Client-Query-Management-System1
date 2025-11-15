CREATE TABLE queries (
  id INT AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(100),
  mobile VARCHAR(15),
  query_heading VARCHAR(255),
  query_description TEXT,
  query_created_time DATETIME,
  query_closed_time DATETIME NULL,
  status ENUM('Open', 'Closed') DEFAULT 'Open',
  created_by VARCHAR(50)
);
SHOW TABLES;
DESCRIBE queries
SELECT * FROM users;
SELECT * FROM queries;
SELECT * FROM queries ORDER BY query_created_time DESC;