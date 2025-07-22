
-- Crear tabla de usuarios
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(100),
    apellido VARCHAR(100),
    email VARCHAR(100),
    balance DECIMAL(10,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Crear tabla de transacciones
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    pin VARCHAR(10),
    transaction_id VARCHAR(100) NOT NULL,
    amount DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Insertar usuario de ejemplo
INSERT INTO users (user_id, nombre, apellido, email, balance) 
VALUES ('USR001', 'Juan', 'Pérez', 'juan@example.com', 150.00)
ON CONFLICT (user_id) DO NOTHING;

-- Insertar algunas transacciones de ejemplo
INSERT INTO transactions (user_id, pin, transaction_id, amount) 
VALUES 
    ('USR001', '8452', 'TX-000001', 50.00),
    ('USR001', '7891', 'TX-000002', 25.00),
    ('USR001', '1234', 'TX-000003', 75.00);
