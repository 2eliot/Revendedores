
-- Migración para agregar game_type a la tabla pins
ALTER TABLE pins ADD COLUMN IF NOT EXISTS game_type VARCHAR(50) DEFAULT 'freefire_latam';

-- Actualizar PINs existentes para que sean de Free Fire Latam por defecto
UPDATE pins SET game_type = 'freefire_latam' WHERE game_type IS NULL OR game_type = '';

-- Crear índice para mejorar performance
CREATE INDEX IF NOT EXISTS idx_pins_game_type ON pins(game_type);
CREATE INDEX IF NOT EXISTS idx_pins_value_game_type ON pins(value, game_type, is_used);
