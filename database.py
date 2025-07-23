import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def connect(self):
        try:
            # Usar DATABASE_URL de los secretos de Replit
            database_url = os.environ.get('DATABASE_URL')
            if database_url:
                self.connection = psycopg2.connect(database_url)
            else:
                # Fallback a variables individuales
                self.connection = psycopg2.connect(
                    host=os.environ.get('DB_HOST'),
                    database=os.environ.get('DB_NAME'),
                    user=os.environ.get('DB_USER'),
                    password=os.environ.get('DB_PASSWORD'),
                    port=os.environ.get('DB_PORT', '5432')
                )
            self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            return True
        except Exception as e:
            print(f"Error conectando a la base de datos: {e}")
            return False

    def disconnect(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    def execute_query(self, query, params=None):
        try:
            self.cursor.execute(query, params)
            self.connection.commit()

            # Solo hacer fetchall() si hay resultados para obtener
            if self.cursor.description is not None:
                return self.cursor.fetchall()
            else:
                # Para queries como UPDATE, INSERT, DELETE sin RETURNING
                return []
        except Exception as e:
            self.connection.rollback()
            print(f"Error ejecutando query: {e}")
            return None

    def insert_transaction(self, user_id, pin, transaction_id, amount=None):
        query = """
        INSERT INTO transactions (user_id, pin, transaction_id, amount, created_at)
        VALUES (%s, %s, %s, %s, NOW())
        RETURNING *
        """
        result = self.execute_query(query, (user_id, pin, transaction_id, amount))
        
        # Limpiar transacciones antiguas después de insertar una nueva
        if result:
            self.cleanup_old_transactions(user_id)
            
        return result

    def get_user_transactions(self, user_id, limit=10, offset=0):
        # Si es admin, obtener todas las transacciones de todos los usuarios
        if user_id == 'ADMIN001':
            query = """
            SELECT t.*, u.nombre, u.apellido 
            FROM transactions t
            LEFT JOIN users u ON t.user_id = u.user_id
            ORDER BY t.created_at DESC 
            LIMIT %s OFFSET %s
            """
            return self.execute_query(query, (limit, offset))
        else:
            # Para usuarios normales, solo sus transacciones
            query = """
            SELECT * FROM transactions 
            WHERE user_id = %s 
            ORDER BY created_at DESC 
            LIMIT %s OFFSET %s
            """
            return self.execute_query(query, (user_id, limit, offset))

    def get_user_balance(self, user_id):
        query = "SELECT balance FROM users WHERE user_id = %s"
        result = self.execute_query(query, (user_id,))
        return result[0]['balance'] if result else 0

    def update_user_balance(self, user_id, new_balance):
        # Obtener el saldo actual antes de actualizar
        current_balance = self.get_user_balance(user_id)

        query = "UPDATE users SET balance = %s WHERE user_id = %s"
        result = self.execute_query(query, (new_balance, user_id))

        # Registrar la transacción de cambio de saldo
        if result is not None:
            difference = float(new_balance) - float(current_balance)
            if difference != 0:  # Solo registrar si hay cambio
                self.insert_transaction(
                    user_id=user_id,
                    pin="ADMIN",
                    transaction_id=f"BALANCE-{user_id}-{int(__import__('time').time())}",
                    amount=difference
                )
                # La limpieza automática ya se ejecuta en insert_transaction

        return result

    def create_user(self, nombre, apellido, telefono, email, password_hash):
        # Obtener el próximo número secuencial
        count_query = "SELECT COUNT(*) FROM users WHERE user_id LIKE 'USR%'"
        count_result = self.execute_query(count_query)

        if count_result:
            user_count = count_result[0]['count'] + 1
        else:
            user_count = 1

        # Crear ID secuencial con formato USR001, USR002, etc.
        user_id = f"USR{user_count:03d}"

        query = """
        INSERT INTO users (user_id, nombre, apellido, telefono, email, password, balance)
        VALUES (%s, %s, %s, %s, %s, %s, 0.00)
        RETURNING user_id, nombre, apellido, email
        """
        return self.execute_query(query, (user_id, nombre, apellido, telefono, email, password_hash))

    def get_user_by_email(self, email):
        query = "SELECT * FROM users WHERE email = %s"
        result = self.execute_query(query, (email,))
        return result[0] if result else None

    def get_user_by_id(self, user_id):
        query = "SELECT * FROM users WHERE user_id = %s"
        result = self.execute_query(query, (user_id,))
        return result[0] if result else None

    def update_admin_credentials(self, email, password_hash):
        query = """
        UPDATE users 
        SET email = %s, password = %s 
        WHERE user_id = 'ADMIN001'
        """
        return self.execute_query(query, (email, password_hash))

    def get_all_users(self):
        query = """
        SELECT user_id, nombre, apellido, telefono, email, balance, 
               created_at, COALESCE(is_active, true) as is_active
        FROM users 
        WHERE user_id != 'ADMIN001'
        ORDER BY created_at DESC
        """
        return self.execute_query(query)

    def toggle_user_status(self, user_id, action):
        is_active = True if action == 'activate' else False
        query = "UPDATE users SET is_active = %s WHERE user_id = %s"
        result = self.execute_query(query, (is_active, user_id))
        return result is not None

    def delete_user(self, user_id):
        # Primero eliminar transacciones del usuario
        delete_transactions = "DELETE FROM transactions WHERE user_id = %s"
        self.execute_query(delete_transactions, (user_id,))

        # Luego eliminar el usuario
        delete_user_query = "DELETE FROM users WHERE user_id = %s"
        result = self.execute_query(delete_user_query, (user_id,))
        return result is not None

    def add_credit_to_user(self, user_id, amount):
        query = """
        UPDATE users 
        SET balance = balance + %s 
        WHERE user_id = %s
        RETURNING balance
        """
        result = self.execute_query(query, (amount, user_id))

        # Registrar la transacción de crédito agregado
        if result is not None and len(result) > 0:
            self.insert_transaction(
                user_id=user_id,
                pin="ADMIN",
                transaction_id=f"CREDIT-{user_id}-{int(__import__('time').time())}",
                amount=amount
            )
            # La limpieza automática ya se ejecuta en insert_transaction

        return result is not None and len(result) > 0

    def create_pin(self, pin_code, value):
        """Crear un nuevo PIN"""
        query = """
        INSERT INTO pins (pin_code, value, created_at)
        VALUES (%s, %s, NOW())
        RETURNING *
        """
        return self.execute_query(query, (pin_code, value))

    def get_available_pin_by_value(self, value):
        """Obtener un PIN disponible del valor específico"""
        query = """
        SELECT * FROM pins 
        WHERE value = %s AND is_used = false 
        ORDER BY created_at ASC 
        LIMIT 1
        """
        result = self.execute_query(query, (value,))
        return result[0] if result else None

    def use_pin(self, pin_id, user_id):
        """Marcar un PIN como usado"""
        query = """
        DELETE FROM pins 
        WHERE id = %s AND is_used = false
        RETURNING *
        """
        result = self.execute_query(query, (pin_id,))
        if result:
          self.insert_transaction(
                user_id=user_id,
                pin="PIN",
                transaction_id=f"PIN-{user_id}-{int(__import__('time').time())}",
                amount=0
            )
        return result

    def get_pins_stats(self):
        """Obtener estadísticas de PINés (solo disponibles ya que los usados se eliminan)"""
        query = """
        SELECT 
            value,
            COUNT(*) as total,
            COUNT(*) as available,
            0 as used
        FROM pins 
        WHERE is_used = false
        GROUP BY value 
        ORDER BY value ASC
        """
        return self.execute_query(query)

    def get_all_pins(self):
        """Obtener todos los PINés"""
        query = """
        SELECT p.*, u.nombre, u.apellido 
        FROM pins p
        LEFT JOIN users u ON p.user_id = u.user_id
        ORDER BY p.created_at DESC
        """
        return self.execute_query(query)

    def get_pin_by_code(self, pin_code):
        """Verificar si un PIN ya existe"""
        query = "SELECT * FROM pins WHERE pin_code = %s"
        result = self.execute_query(query, (pin_code,))
        return result[0] if result else None

    def get_pin_from_provider(self, amount_value):
        """Obtener PIN del proveedor API para Free Fire Latam"""
        import requests
        import os
        
        # Obtener credenciales del proveedor desde secretos
        provider_user = os.getenv('PROVIDER_USER')
        provider_password = os.getenv('PROVIDER_PASSWORD')
        
        if not provider_user or not provider_password:
            print("Error: Credenciales del proveedor no configuradas")
            return None
        
        # URL de la API del proveedor
        api_url = "https://inefableshop.net/conexion_api/api.php"
        
        # Mapeo correcto de valores locales (1-9) a valores de la API del proveedor
        provider_amount_mapping = {
            1: 'FFCH100',    # 110 💎 / $0.66
            2: 'FFCH300',    # 341 💎 / $1.99  
            3: 'FFCH500',    # 572 💎 / $3.35
            4: 'FFCH1000',   # 1.166 💎 / $6.70
            5: 'FFCH2000',   # 2.376 💎 / $12.70
            6: 'FFCH5000',   # 6.138 💎 / $29.50
            7: 'FFMP1',      # Tarjeta básica / $0.40
            8: 'FFMP7',      # Tarjeta semanal / $1.40
            9: 'FFMP30'      # Tarjeta mensual / $6.50
        }
        
        # Obtener el valor correcto para la API del proveedor
        provider_amount = provider_amount_mapping.get(amount_value)
        
        if not provider_amount:
            print(f"Valor {amount_value} no válido para la API del proveedor")
            return None
        
        # Parámetros para la solicitud
        params = {
            'action': 'recarga',
            'usuario': provider_user,
            'clave': provider_password,
            'tipo': 'recargaPinFreefire',
            'monto': provider_amount,
            'numero': '0'
        }
        
        try:
            # Realizar solicitud a la API del proveedor
            print(f"Consultando API del proveedor con parámetros: {params}")
            response = requests.get(api_url, params=params, timeout=30)
            response.raise_for_status()
            
            # La respuesta puede ser JSON o texto plano
            response_data = response.text.strip()
            print(f"Respuesta completa de la API: {response_data}")
            
            # Intentar parsear como JSON primero
            try:
                import json
                json_response = json.loads(response_data)
                
                # Verificar si la respuesta JSON indica éxito
                if json_response.get('ALERTA') == 'VERDE' and json_response.get('PIN'):
                    pin_code = json_response['PIN'].upper().strip()
                    
                    # Validar que el PIN tenga un formato válido
                    if len(pin_code) >= 4 and len(pin_code) <= 20:
                        return {
                            'pin_code': pin_code,
                            'value': amount_value,
                            'source': 'provider_api'
                        }
                    else:
                        print(f"PIN recibido del proveedor tiene formato inválido: {pin_code}")
                        return None
                else:
                    # La API devolvió un error
                    error_msg = json_response.get('MENSAJE', 'Error desconocido')
                    print(f"Error de la API del proveedor: {error_msg}")
                    return None
                    
            except json.JSONDecodeError:
                # Si no es JSON, asumir que es un PIN en texto plano
                # Limpiar la respuesta de posibles etiquetas HTML
                clean_response = response_data
                
                # Remover advertencias de PHP si existen
                if '<BR />' in clean_response or '<B>WARNING</B>' in clean_response:
                    # Buscar el PIN después de las advertencias
                    lines = clean_response.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('<') and len(line) >= 4 and len(line) <= 20:
                            pin_code = line.upper().strip()
                            return {
                                'pin_code': pin_code,
                                'value': amount_value,
                                'source': 'provider_api'
                            }
                    print(f"No se pudo extraer PIN válido de la respuesta: {clean_response}")
                    return None
                else:
                    # Respuesta en texto plano limpia
                    if len(clean_response) >= 4 and len(clean_response) <= 20:
                        pin_code = clean_response.upper().strip()
                        return {
                            'pin_code': pin_code,
                            'value': amount_value,
                            'source': 'provider_api'
                        }
                    else:
                        print(f"Respuesta inválida del proveedor: {clean_response}")
                        return None
                
        except requests.exceptions.RequestException as e:
            print(f"Error al conectar con el proveedor de PINs: {e}")
            return None
        except Exception as e:
            print(f"Error inesperado al obtener PIN del proveedor: {e}")
            return None

    def cleanup_old_transactions(self, user_id, max_transactions=30):
        """Eliminar transacciones antiguas si el usuario tiene más del máximo permitido"""
        # Contar transacciones del usuario
        count_query = "SELECT COUNT(*) FROM transactions WHERE user_id = %s"
        count_result = self.execute_query(count_query, (user_id,))
        
        if count_result and count_result[0]['count'] > max_transactions:
            # Eliminar las transacciones más antiguas, dejando solo las últimas max_transactions
            delete_query = """
            DELETE FROM transactions 
            WHERE user_id = %s 
            AND id NOT IN (
                SELECT id FROM (
                    SELECT id FROM transactions 
                    WHERE user_id = %s 
                    ORDER BY created_at DESC 
                    LIMIT %s
                ) AS recent_transactions
            )
            """
            result = self.execute_query(delete_query, (user_id, user_id, max_transactions))
            return result is not None
        
        return True