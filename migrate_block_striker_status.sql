
-- Agregar columna status para transacciones de Block Striker
ALTER TABLE transactions 
ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT NULL;

-- Crear índice para mejorar consultas por status
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);
