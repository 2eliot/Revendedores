
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def setup_database():
    try:
        # Conectar a la base de datos
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("Error: DATABASE_URL no está configurada")
            return False
            
        connection = psycopg2.connect(database_url)
        cursor = connection.cursor()
        
        print("Conectado a la base de datos exitosamente")
        
        # Crear tabla de usuarios
        cursor.execute("""
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
        """)
        print("Tabla 'users' creada/verificada")
        
        # Crear tabla de transacciones
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(50) NOT NULL,
            pin VARCHAR(10),
            transaction_id VARCHAR(100) NOT NULL,
            amount DECIMAL(10,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
        """)
        print("Tabla 'transactions' creada/verificada")
        
        connection.commit()
        print("✅ Base de datos configurada exitosamente")
        print("Las tablas están listas para usar")
        
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        print(f"Error configurando la base de datos: {e}")
        return False

if __name__ == "__main__":
    setup_database()
