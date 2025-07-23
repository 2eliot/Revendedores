
import os
from database import Database

def apply_migration():
    """Aplicar migración para agregar columnas de Block Striker"""
    db = Database()
    if not db.connect():
        print("Error: No se pudo conectar a la base de datos")
        return False
    
    try:
        # Leer el archivo de migración
        with open('migrate_transactions.sql', 'r') as f:
            migration_sql = f.read()
        
        # Ejecutar cada comando de la migración
        commands = migration_sql.split(';')
        for command in commands:
            command = command.strip()
            if command:
                print(f"Ejecutando: {command}")
                result = db.execute_query(command)
                if result is None:
                    print(f"Error ejecutando comando: {command}")
                    return False
        
        print("✅ Migración aplicada exitosamente")
        return True
        
    except Exception as e:
        print(f"Error aplicando migración: {e}")
        return False
    finally:
        db.disconnect()

if __name__ == "__main__":
    apply_migration()
