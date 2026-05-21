CREATE TABLE IF NOT EXISTS products (
    product_id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    price DECIMAL(10,2) NOT NULL
);

INSERT INTO products VALUES
(1,'Laptop Pro 15','Electronics',1299.99),
(2,'Wireless Mouse','Electronics',29.99),
(3,'Ergonomic Desk Chair','Furniture',249.99),
(4,'Coffee Mug XL','Kitchen',14.99),
(5,'USB-C Cable 2m','Electronics',12.99),
(6,'Gaming Keyboard RGB','Electronics',89.99),
(7,'Smartphone Stand','Accessories',19.99),
(8,'Bluetooth Speaker','Electronics',79.99),
(9,'Office Desk','Furniture',399.99),
(10,'Notebook Pack','Stationery',9.99),
(11,'LED Monitor 27','Electronics',299.99),
(12,'Water Bottle Steel','Kitchen',24.99)
ON CONFLICT (product_id) DO NOTHING;



CREATE TABLE IF NOT EXISTS sales (
    sale_id INT PRIMARY KEY,
    product_id INT REFERENCES products(product_id),
    sale_date TIMESTAMP,
    quantity INT,
    total_amount DECIMAL(10,2)
);

INSERT INTO sales VALUES
(1,1,NOW(),1,1299.99),
(2,2,NOW(),2,59.98),
(3,3,NOW(),1,249.99),
(4,4,NOW(),3,44.97),
(5,5,NOW(),2,25.98),
(6,6,NOW(),1,89.99),
(7,7,NOW(),4,79.96),
(8,8,NOW(),2,159.98),
(9,9,NOW(),1,399.99),
(10,10,NOW(),5,49.95),
(11,11,NOW(),2,599.98),
(12,12,NOW(),3,74.97),
(13,1,NOW(),1,1299.99),
(14,6,NOW(),2,179.98),
(15,8,NOW(),1,79.99)
ON CONFLICT (sale_id) DO NOTHING;



CREATE TABLE IF NOT EXISTS reviews (
    review_id INT PRIMARY KEY,
    product_id INT REFERENCES products(product_id),
    rating INT,
    review_text TEXT
);

INSERT INTO reviews VALUES
(1,1,5,'Excellent laptop'),
(2,2,4,'Good mouse'),
(3,3,5,'Very comfortable chair'),
(4,4,4,'Nice mug'),
(5,5,5,'Durable cable'),
(6,6,5,'Amazing keyboard'),
(7,7,4,'Useful stand'),
(8,8,5,'Great sound quality'),
(9,9,4,'Spacious desk'),
(10,10,4,'Good notebooks'),
(11,11,5,'Crystal clear display'),
(12,12,5,'Keeps water cold')
ON CONFLICT (review_id) DO NOTHING;