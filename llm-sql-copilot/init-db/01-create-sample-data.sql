-- Create sample e-commerce database

-- Customers table
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    address VARCHAR(200),
    city VARCHAR(50),
    state VARCHAR(2),
    zip_code VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    price DECIMAL(10, 2) NOT NULL,
    stock_quantity INT DEFAULT 0,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders table
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(customer_id),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending',
    total_amount DECIMAL(10, 2),
    shipping_address VARCHAR(200),
    CONSTRAINT fk_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Order Items table
CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(order_id),
    product_id INT REFERENCES products(product_id),
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(10, 2) NOT NULL,
    CONSTRAINT fk_order FOREIGN KEY (order_id) REFERENCES orders(order_id),
    CONSTRAINT fk_product FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Insert sample customers
INSERT INTO customers (first_name, last_name, email, phone, address, city, state, zip_code) VALUES
('John', 'Doe', 'john.doe@email.com', '555-0101', '123 Main St', 'San Francisco', 'CA', '94102'),
('Jane', 'Smith', 'jane.smith@email.com', '555-0102', '456 Oak Ave', 'Los Angeles', 'CA', '90001'),
('Bob', 'Johnson', 'bob.johnson@email.com', '555-0103', '789 Pine Rd', 'New York', 'NY', '10001'),
('Alice', 'Williams', 'alice.williams@email.com', '555-0104', '321 Elm St', 'Chicago', 'IL', '60601'),
('Charlie', 'Brown', 'charlie.brown@email.com', '555-0105', '654 Maple Dr', 'Houston', 'TX', '77001'),
('Diana', 'Davis', 'diana.davis@email.com', '555-0106', '987 Cedar Ln', 'Phoenix', 'AZ', '85001'),
('Eve', 'Miller', 'eve.miller@email.com', '555-0107', '147 Birch Ct', 'Philadelphia', 'PA', '19101'),
('Frank', 'Wilson', 'frank.wilson@email.com', '555-0108', '258 Spruce Way', 'San Antonio', 'TX', '78201'),
('Grace', 'Moore', 'grace.moore@email.com', '555-0109', '369 Ash Blvd', 'San Diego', 'CA', '92101'),
('Henry', 'Taylor', 'henry.taylor@email.com', '555-0110', '741 Walnut St', 'Dallas', 'TX', '75201');

-- Insert sample products
INSERT INTO products (product_name, category, price, stock_quantity, description) VALUES
('Laptop Pro 15', 'Electronics', 1299.99, 50, 'High-performance laptop with 16GB RAM'),
('Wireless Mouse', 'Electronics', 29.99, 200, 'Ergonomic wireless mouse'),
('USB-C Hub', 'Electronics', 49.99, 150, '7-in-1 USB-C hub with HDMI'),
('Coffee Maker', 'Home & Kitchen', 79.99, 75, 'Programmable coffee maker'),
('Desk Lamp', 'Home & Kitchen', 39.99, 100, 'LED desk lamp with adjustable brightness'),
('Office Chair', 'Furniture', 249.99, 30, 'Ergonomic office chair with lumbar support'),
('Standing Desk', 'Furniture', 399.99, 20, 'Adjustable height standing desk'),
('Notebook Set', 'Office Supplies', 15.99, 300, 'Pack of 5 premium notebooks'),
('Pen Set', 'Office Supplies', 12.99, 250, 'Set of 10 ballpoint pens'),
('Water Bottle', 'Sports', 24.99, 180, 'Insulated stainless steel water bottle'),
('Yoga Mat', 'Sports', 34.99, 120, 'Non-slip yoga mat with carrying strap'),
('Backpack', 'Accessories', 59.99, 90, 'Waterproof laptop backpack'),
('Headphones', 'Electronics', 149.99, 85, 'Noise-cancelling wireless headphones'),
('Webcam HD', 'Electronics', 89.99, 60, '1080p webcam with built-in microphone'),
('Keyboard Mechanical', 'Electronics', 119.99, 45, 'RGB mechanical gaming keyboard');

-- Insert sample orders
INSERT INTO orders (customer_id, order_date, status, total_amount, shipping_address) VALUES
(1, '2024-01-15 10:30:00', 'delivered', 1379.97, '123 Main St, San Francisco, CA 94102'),
(2, '2024-01-16 14:20:00', 'delivered', 164.97, '456 Oak Ave, Los Angeles, CA 90001'),
(3, '2024-01-17 09:15:00', 'shipped', 649.98, '789 Pine Rd, New York, NY 10001'),
(4, '2024-01-18 11:45:00', 'delivered', 59.98, '321 Elm St, Chicago, IL 60601'),
(1, '2024-01-19 16:30:00', 'processing', 399.99, '123 Main St, San Francisco, CA 94102'),
(5, '2024-01-20 13:00:00', 'delivered', 79.99, '654 Maple Dr, Houston, TX 77001'),
(6, '2024-01-21 10:00:00', 'shipped', 249.99, '987 Cedar Ln, Phoenix, AZ 85001'),
(7, '2024-01-22 15:30:00', 'delivered', 44.98, '147 Birch Ct, Philadelphia, PA 19101'),
(8, '2024-01-23 12:15:00', 'processing', 1299.99, '258 Spruce Way, San Antonio, TX 78201'),
(9, '2024-01-24 14:45:00', 'delivered', 269.97, '369 Ash Blvd, San Diego, CA 92101'),
(10, '2024-01-25 09:30:00', 'shipped', 149.99, '741 Walnut St, Dallas, TX 75201'),
(2, '2024-01-26 11:00:00', 'delivered', 119.99, '456 Oak Ave, Los Angeles, CA 90001'),
(3, '2024-01-27 16:15:00', 'processing', 89.99, '789 Pine Rd, New York, NY 10001'),
(4, '2024-01-28 10:30:00', 'delivered', 399.99, '321 Elm St, Chicago, IL 60601'),
(5, '2024-01-29 13:45:00', 'shipped', 649.96, '654 Maple Dr, Houston, TX 77001');

-- Insert sample order items
INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal) VALUES
-- Order 1
(1, 1, 1, 1299.99, 1299.99),
(1, 2, 1, 29.99, 29.99),
(1, 3, 1, 49.99, 49.99),
-- Order 2
(2, 13, 1, 149.99, 149.99),
(2, 9, 1, 12.99, 12.99),
-- Order 3
(3, 6, 2, 249.99, 499.98),
(3, 5, 3, 39.99, 119.97),
-- Order 4
(4, 10, 2, 24.99, 49.98),
(4, 8, 1, 15.99, 15.99),
-- Order 5
(5, 7, 1, 399.99, 399.99),
-- Order 6
(6, 4, 1, 79.99, 79.99),
-- Order 7
(7, 6, 1, 249.99, 249.99),
-- Order 8
(8, 11, 1, 34.99, 34.99),
(8, 8, 1, 15.99, 15.99),
-- Order 9
(9, 1, 1, 1299.99, 1299.99),
-- Order 10
(10, 12, 3, 59.99, 179.97),
(10, 2, 3, 29.99, 89.97),
-- Order 11
(11, 13, 1, 149.99, 149.99),
-- Order 12
(12, 15, 1, 119.99, 119.99),
-- Order 13
(13, 14, 1, 89.99, 89.99),
-- Order 14
(14, 7, 1, 399.99, 399.99),
-- Order 15
(15, 6, 2, 249.99, 499.98),
(15, 5, 1, 39.99, 39.99);

-- Create useful views
CREATE VIEW customer_order_summary AS
SELECT 
    c.customer_id,
    c.first_name,
    c.last_name,
    c.email,
    COUNT(o.order_id) as total_orders,
    SUM(o.total_amount) as total_spent,
    AVG(o.total_amount) as avg_order_value,
    MAX(o.order_date) as last_order_date
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.first_name, c.last_name, c.email;

CREATE VIEW product_sales_summary AS
SELECT 
    p.product_id,
    p.product_name,
    p.category,
    p.price,
    p.stock_quantity,
    COALESCE(SUM(oi.quantity), 0) as total_sold,
    COALESCE(SUM(oi.subtotal), 0) as total_revenue
FROM products p
LEFT JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY p.product_id, p.product_name, p.category, p.price, p.stock_quantity;

-- Create indexes for better query performance
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_order_date ON orders(order_date);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_products_category ON products(category);