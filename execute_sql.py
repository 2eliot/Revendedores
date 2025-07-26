
import os
import psycopg2
from database import Database

def execute_sql_file(filename):
    """Ejecutar un archivo SQL completo"""
    db = Database()
    if not db.connect():
        print("❌ Error: No se pudo conectar a la base de datos")
        return False
    
    try:
        if os.path.exists(filename):
            print(f"📄 Ejecutando archivo SQL: {filename}")
            with open(filename, 'r', encoding='utf-8') as f:
                sql_content = f.read()
                
            # Dividir comandos por punto y coma y filtrar comentarios
            commands = []
            current_command = ""
            
            for line in sql_content.split('\n'):
                line = line.strip()
                if line and not line.startswith('--'):
                    current_command += line + " "
                    if line.endswith(';'):
                        commands.append(current_command.strip())
                        current_command = ""
            
            # Agregar último comando si no termina en ;
            if current_command.strip():
                commands.append(current_command.strip())
            
            # Ejecutar comandos
            for i, command in enumerate(commands):
                if command:
                    print(f"📝 Ejecutando comando {i+1}/{len(commands)}: {command[:100]}...")
                    result = db.execute_query(command)
                    if result is None:
                        print(f"❌ Error ejecutando comando {i+1}")
                        return False
            
            print("✅ Esquema SQL ejecutado exitosamente")
            return True
        else:
            print(f"❌ Error: Archivo {filename} no encontrado")
            return False
            
    except Exception as e:
        print(f"❌ Error ejecutando SQL: {e}")
        return False
    finally:
        db.disconnect()

def initialize_database():
    """Inicializar la base de datos con el esquema completo"""
    print("🚀 Inicializando base de datos con esquema completo...")
    
    # Ejecutar el esquema principal
    if execute_sql_file('database_schema.sql'):
        print("✅ Base de datos inicializada correctamente")
        print("📊 La web ahora usará solo la base de datos pura")
        return True
    else:
        print("❌ Error inicializando la base de datos")
        return False

if __name__ == "__main__":
    initialize_database()
