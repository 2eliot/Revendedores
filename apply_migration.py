
import os
from database import Database

def apply_migration():
    """Aplicar migración para agregar columnas de Block Striker"""
    db = Database()
    if not db.connect():
        print("Error: No se pudo conectar a la base de datos")
        return False
    
    try:
        # Leer los archivos de migración
        migration_files = ['migrate_transactions.sql', 'migrate_block_striker_status.sql']
        
        for file_name in migration_files:
            if os.path.exists(file_name):
                print(f"Aplicando migración: {file_name}")
                with open(file_name, 'r') as f:
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
        
        print("✅ Todas las migraciones aplicadas exitosamente")
        return True
        
    except Exception as e:
        print(f"Error aplicando migración: {e}")
        return False
    finally:
        db.disconnect()

if __name__ == "__main__":
    apply_migration()
