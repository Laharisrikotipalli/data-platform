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
(5,'USB-C Cable 2m','Electronics',12.99)
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
(5,5,NOW(),2,25.98)
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
(3,3,5,'Very comfortable'),
(4,4,4,'Nice mug'),
(5,5,5,'Durable cable')
ON CONFLICT (review_id) DO NOTHING;