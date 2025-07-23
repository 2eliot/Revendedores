
-- Agregar columnas para información específica de juegos
ALTER TABLE transactions 
ADD COLUMN IF NOT EXISTS player_id VARCHAR(100),
ADD COLUMN IF NOT EXISTS game_type VARCHAR(50),
ADD COLUMN IF NOT EXISTS option_value INTEGER;

-- Crear índice para mejorar consultas por juego
CREATE INDEX IF NOT EXISTS idx_transactions_game_type ON transactions(game_type);
CREATE INDEX IF NOT EXISTS idx_transactions_player_id ON transactions(player_id);
