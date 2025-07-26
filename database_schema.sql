
-- ============================================
-- ESQUEMA COMPLETO DE BASE DE DATOS
-- InefableStore - Sistema de Recargas de Juegos
-- ============================================

-- Eliminar tablas existentes (opcional - comentar si no quieres resetear)
-- DROP TABLE IF EXISTS game_prices CASCADE;
-- DROP TABLE IF EXISTS transactions CASCADE;
-- DROP TABLE IF EXISTS pins CASCADE;
-- DROP TABLE IF EXISTS users CASCADE;

-- ============================================
-- TABLA DE USUARIOS
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    telefono VARCHAR(20),
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    balance DECIMAL(10,2) DEFAULT 0.00 CHECK (balance >= 0),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para optimizar consultas de usuarios
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);

-- ============================================
-- TABLA DE TRANSACCIONES
-- ============================================
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    pin VARCHAR(20),
    transaction_id VARCHAR(100) UNIQUE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    game_type VARCHAR(50) DEFAULT 'freefire_latam',
    option_value INTEGER,
    player_id VARCHAR(100), -- Para Block Striker
    status VARCHAR(20) DEFAULT 'completado', -- completado, procesando, rechazado
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Restricciones
    CONSTRAINT fk_transactions_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT chk_transaction_status CHECK (status IN ('completado', 'procesando', 'rechazado')),
    CONSTRAINT chk_game_type CHECK (game_type IN ('freefire_latam', 'freefire_global', 'Block Striker'))
);

-- Índices para optimizar consultas de transacciones
CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);
CREATE INDEX IF NOT EXISTS idx_transactions_game_type ON transactions(game_type);
CREATE INDEX IF NOT EXISTS idx_transactions_transaction_id ON transactions(transaction_id);

-- ============================================
-- TABLA DE PINES (CÓDIGOS DE RECARGA)
-- ============================================
CREATE TABLE IF NOT EXISTS pins (
    id SERIAL PRIMARY KEY,
    pin_code VARCHAR(20) UNIQUE NOT NULL,
    value INTEGER NOT NULL CHECK (value > 0),
    game_type VARCHAR(50) DEFAULT 'freefire_latam',
    is_used BOOLEAN DEFAULT false,
    user_id VARCHAR(50) NULL,
    used_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Restricciones
    CONSTRAINT fk_pins_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL,
    CONSTRAINT chk_pins_game_type CHECK (game_type IN ('freefire_latam', 'freefire_global', 'block_striker'))
);

-- Índices para optimizar consultas de pines
CREATE INDEX IF NOT EXISTS idx_pins_value_game_type ON pins(value, game_type) WHERE is_used = false;
CREATE INDEX IF NOT EXISTS idx_pins_is_used ON pins(is_used);
CREATE INDEX IF NOT EXISTS idx_pins_game_type ON pins(game_type);
CREATE INDEX IF NOT EXISTS idx_pins_created_at ON pins(created_at DESC);

-- ============================================
-- TABLA DE PRECIOS DE JUEGOS
-- ============================================
CREATE TABLE IF NOT EXISTS game_prices (
    id SERIAL PRIMARY KEY,
    game_type VARCHAR(50) NOT NULL,
    option_key VARCHAR(10) NOT NULL,
    price DECIMAL(10,2) NOT NULL CHECK (price > 0),
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Restricciones
    CONSTRAINT uk_game_prices_type_key UNIQUE(game_type, option_key),
    CONSTRAINT chk_price_game_type CHECK (game_type IN ('freefire_latam', 'freefire_global', 'block_striker'))
);

-- Índices para optimizar consultas de precios
CREATE INDEX IF NOT EXISTS idx_game_prices_type ON game_prices(game_type);
CREATE INDEX IF NOT EXISTS idx_game_prices_active ON game_prices(is_active);

-- ============================================
-- TABLA DE CONFIGURACIONES DEL SISTEMA
-- ============================================
CREATE TABLE IF NOT EXISTS system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- DATOS INICIALES
-- ============================================

-- Insertar usuario administrador
INSERT INTO users (user_id, nombre, apellido, telefono, email, password, balance) 
VALUES ('ADMIN001', 'Admin', 'Sistema', '000000000', 'admin@gmail.com', 'temp_password', 0.00)
ON CONFLICT (user_id) DO NOTHING;

-- Insertar usuario de ejemplo
INSERT INTO users (user_id, nombre, apellido, telefono, email, password, balance) 
VALUES ('USR001', 'Usuario', 'Ejemplo', '123456789', 'usuario@example.com', 'scrypt:32768:8:1$salt$hash', 50.00)
ON CONFLICT (user_id) DO NOTHING;

-- ============================================
-- PRECIOS INICIALES DE LOS JUEGOS
-- ============================================

-- Precios Free Fire Latam
INSERT INTO game_prices (game_type, option_key, price, description) VALUES
('freefire_latam', '1', 0.69, '110 💎'),
('freefire_latam', '2', 2.15, '341 💎'),
('freefire_latam', '3', 3.55, '572 💎'),
('freefire_latam', '4', 6.99, '1.166 💎'),
('freefire_latam', '5', 14.44, '2.376 💎'),
('freefire_latam', '6', 32.11, '6.138 💎'),
('freefire_latam', '7', 0.5, 'Tarjeta básica'),
('freefire_latam', '8', 1.5, 'Tarjeta semanal'),
('freefire_latam', '9', 7.1, 'Tarjeta mensual')
ON CONFLICT (game_type, option_key) DO UPDATE SET 
    price = EXCLUDED.price,
    description = EXCLUDED.description,
    updated_at = CURRENT_TIMESTAMP;

-- Precios Free Fire Global
INSERT INTO game_prices (game_type, option_key, price, description) VALUES
('freefire_global', '1', 0.86, '100+10 diamantes'),
('freefire_global', '2', 2.9, '310+31 diamantes'),
('freefire_global', '3', 4.0, '520+52 diamantes'),
('freefire_global', '4', 7.75, '1.060+106 diamantes'),
('freefire_global', '5', 15.3, '2.180+218 diamantes'),
('freefire_global', '6', 38.0, '5.600+560 diamantes')
ON CONFLICT (game_type, option_key) DO UPDATE SET 
    price = EXCLUDED.price,
    description = EXCLUDED.description,
    updated_at = CURRENT_TIMESTAMP;

-- Precios Block Striker
INSERT INTO game_prices (game_type, option_key, price, description) VALUES
('block_striker', '1', 0.82, '200 monedas'),
('block_striker', '2', 2.6, '600 monedas'),
('block_striker', '3', 4.3, '1.200 monedas'),
('block_striker', '4', 8.65, '2.400 monedas'),
('block_striker', '5', 17.3, '5.000 monedas'),
('block_striker', '6', 43.15, '12.000 monedas'),
('block_striker', '7', 3.5, 'Pase de batalla'),
('block_striker', '8', 8.0, 'Pack premium'),
('block_striker', '9', 1.85, 'Caja misteriosa')
ON CONFLICT (game_type, option_key) DO UPDATE SET 
    price = EXCLUDED.price,
    description = EXCLUDED.description,
    updated_at = CURRENT_TIMESTAMP;

-- ============================================
-- CONFIGURACIONES DEL SISTEMA
-- ============================================
INSERT INTO system_config (config_key, config_value, description) VALUES
('banner_message', '🎮 ¡Bienvenido a InefableStore! Tu tienda de recargas de juegos más confiable 💎', 'Mensaje del banner principal'),
('maintenance_mode', 'false', 'Modo de mantenimiento del sistema'),
('max_transactions_per_user', '30', 'Máximo de transacciones a mantener por usuario'),
('freefire_latam_api_enabled', 'true', 'Habilitar API de Free Fire Latam'),
('freefire_global_api_enabled', 'false', 'Habilitar API de Free Fire Global'),
('block_striker_api_enabled', 'false', 'Habilitar API de Block Striker')
ON CONFLICT (config_key) DO UPDATE SET 
    config_value = EXCLUDED.config_value,
    updated_at = CURRENT_TIMESTAMP;

-- ============================================
-- PINES DE EJEMPLO (OPCIONAL)
-- ============================================
INSERT INTO pins (pin_code, value, game_type) VALUES
('FF2024A1', 1, 'freefire_latam'),
('FF2024A2', 2, 'freefire_latam'),
('FF2024A3', 3, 'freefire_latam'),
('FG2024B1', 1, 'freefire_global'),
('FG2024B2', 2, 'freefire_global'),
('BS2024C1', 1, 'block_striker'),
('BS2024C2', 2, 'block_striker')
ON CONFLICT (pin_code) DO NOTHING;

-- ============================================
-- TRANSACCIONES DE EJEMPLO
-- ============================================
INSERT INTO transactions (user_id, pin, transaction_id, amount, game_type, option_value, status) VALUES
('USR001', 'FF2024A1', 'TX-USR001-001', -0.69, 'freefire_latam', 1, 'completado'),
('USR001', 'ADMIN', 'CR-USR001-002', 50.00, 'freefire_latam', NULL, 'completado'),
('USR001', 'FF2024A2', 'TX-USR001-003', -2.15, 'freefire_latam', 2, 'completado')
ON CONFLICT (transaction_id) DO NOTHING;

-- ============================================
-- FUNCIONES Y TRIGGERS (OPCIONAL)
-- ============================================

-- Función para actualizar timestamp automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para actualizar updated_at en users
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger para actualizar updated_at en system_config
CREATE TRIGGER update_config_updated_at 
    BEFORE UPDATE ON system_config 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- VISTAS ÚTILES
-- ============================================

-- Vista de estadísticas de usuarios
CREATE OR REPLACE VIEW user_stats AS
SELECT 
    u.user_id,
    u.nombre,
    u.apellido,
    u.balance,
    COUNT(t.id) as total_transactions,
    COALESCE(SUM(CASE WHEN t.amount < 0 THEN ABS(t.amount) ELSE 0 END), 0) as total_spent,
    COALESCE(SUM(CASE WHEN t.amount > 0 THEN t.amount ELSE 0 END), 0) as total_credits,
    MAX(t.created_at) as last_transaction_date
FROM users u
LEFT JOIN transactions t ON u.user_id = t.user_id
WHERE u.user_id != 'ADMIN001'
GROUP BY u.user_id, u.nombre, u.apellido, u.balance;

-- Vista de estadísticas de pines
CREATE OR REPLACE VIEW pin_stats AS
SELECT 
    game_type,
    value,
    COUNT(*) as total_pins,
    COUNT(*) FILTER (WHERE is_used = false) as available_pins,
    COUNT(*) FILTER (WHERE is_used = true) as used_pins
FROM pins
GROUP BY game_type, value
ORDER BY game_type, value;

-- Vista de transacciones recientes
CREATE OR REPLACE VIEW recent_transactions AS
SELECT 
    t.*,
    u.nombre,
    u.apellido,
    gp.description as option_description
FROM transactions t
LEFT JOIN users u ON t.user_id = u.user_id
LEFT JOIN game_prices gp ON t.game_type = gp.game_type AND t.option_value::text = gp.option_key
ORDER BY t.created_at DESC;

-- ============================================
-- COMENTARIOS FINALES
-- ============================================

COMMENT ON TABLE users IS 'Tabla de usuarios del sistema';
COMMENT ON TABLE transactions IS 'Historial de todas las transacciones realizadas';
COMMENT ON TABLE pins IS 'Códigos PIN disponibles y usados';
COMMENT ON TABLE game_prices IS 'Precios configurables para cada juego';
COMMENT ON TABLE system_config IS 'Configuraciones generales del sistema';

-- Verificar que todo se creó correctamente
SELECT 'Base de datos configurada exitosamente' as status;
