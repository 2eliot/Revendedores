-- Crear tabla de usuarios
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(100),
    apellido VARCHAR(100),
    telefono VARCHAR(20),
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    balance DECIMAL(10,2) DEFAULT 0.00,
    is_active BOOLEAN DEFAULT true,
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
INSERT INTO users (user_id, nombre, apellido, telefono, email, password, balance) 
VALUES ('USR001', 'Juan', 'Pérez', '123456789', 'juan@example.com', 'scrypt:32768:8:1$salt$hash', 150.00)
ON CONFLICT (user_id) DO NOTHING;

-- Insertar algunas transacciones de ejemplo
INSERT INTO transactions (user_id, pin, transaction_id, amount) 
VALUES 
    ('USR001', '8452', 'TX-000001', 50.00),
    ('USR001', '7891', 'TX-000002', 25.00),
    ('USR001', '1234', 'TX-000003', 75.00);

-- Insertar usuario administrador simple
INSERT INTO users (user_id, nombre, apellido, telefono, email, password, balance) 
VALUES ('ADMIN001', 'Admin', 'Usuario', '000000000', 'admin', 'temp_password', 0.00)
ON CONFLICT (user_id) DO NOTHING;