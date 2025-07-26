import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import urllib.parse

load_dotenv()

class Database:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def connect(self):
        """Establecer conexión con la base de datos"""
        try:
            # Primero intentar usar DATABASE_URL (para Render)
            database_url = os.getenv('DATABASE_URL')

            if database_url:
                # Parsear la URL de la base de datos
                url = urllib.parse.urlparse(database_url)
                self.connection = psycopg2.connect(
                    host=url.hostname,
                    database=url.path[1:],  # Remover el '/' inicial
                    user=url.username,
                    password=url.password,
                    port=url.port,
                    cursor_factory=RealDictCursor
                )
                self.cursor = self.connection.cursor()
            else:
                # Usar credenciales individuales (para desarrollo local)
                host = os.getenv('DB_HOST', 'localhost')
                database = os.getenv('DB_NAME', 'flask_app')
                user = os.getenv('DB_USER', 'postgres')
                password = os.getenv('DB_PASSWORD', '')
                port = os.getenv('DB_PORT', '5432')

                self.connection = psycopg2.connect(
                    host=host,
                    database=database,
                    user=user,
                    password=password,
                    port=port,
                    cursor_factory=RealDictCursor
                )
                self.cursor = self.connection.cursor()
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
            ORDER BY 
                CASE WHEN t.status = 'procesando' THEN 0 ELSE 1 END,
                t.created_at DESC 
            LIMIT %s OFFSET %s
            """
            return self.execute_query(query, (limit, offset))
        else:
            # Para usuarios normales, solo sus transacciones
            query = """
            SELECT * FROM transactions 
            WHERE user_id = %s 
            ORDER BY 
                CASE WHEN status = 'procesando' THEN 0 ELSE 1 END,
                created_at DESC 
            LIMIT %s OFFSET %s
            """
            return self.execute_query(query, (user_id, limit, offset))

    def get_user_balance(self, user_id):
        query = "SELECT balance FROM users WHERE user_id = %s"
        result = self.execute_query(query, (user_id,))
        return result[0]['balance'] if result and len(result) > 0 else "0.00"

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
                    transaction_id=f"AD{user_id[-3:]}{int(__import__('time').time()) % 10000}",
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
                transaction_id=f"CR{user_id[-3:]}{int(__import__('time').time()) % 10000}",
                amount=amount
            )
            # La limpieza automática ya se ejecuta en insert_transaction

        return result is not None and len(result) > 0

    def create_pin(self, pin_code, value, game_type='freefire_latam'):
        """Crear un nuevo PIN con tipo de juego específico"""
        # Crear tabla con columna game_type si no existe
        create_table_query = """
        CREATE TABLE IF NOT EXISTS pins (
            id SERIAL PRIMARY KEY,
            pin_code VARCHAR(20) NOT NULL UNIQUE,
            value INTEGER NOT NULL,
            is_used BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            game_type VARCHAR(50) DEFAULT 'freefire_latam'
        )
        """
        self.execute_query(create_table_query)

        # Agregar columna game_type si no existe (para compatibilidad)
        add_column_query = """
        ALTER TABLE pins 
        ADD COLUMN IF NOT EXISTS game_type VARCHAR(50) DEFAULT 'freefire_latam'
        """
        self.execute_query(add_column_query)

        query = """
        INSERT INTO pins (pin_code, value, game_type, created_at)
        VALUES (%s, %s, %s, NOW())
        RETURNING *
        """
        return self.execute_query(query, (pin_code, value, game_type))

    def get_available_pin_by_value(self, value, game_type='freefire_latam'):
        """Obtener un PIN disponible del valor específico y tipo de juego"""
        query = """
        SELECT * FROM pins 
        WHERE value = %s AND is_used = false AND game_type = %s
        ORDER BY created_at ASC 
        LIMIT 1
        """
        result = self.execute_query(query, (value, game_type))
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
                transaction_id=f"PN{user_id[-3:]}{int(__import__('time').time()) % 10000}",
                amount=0
            )
        return result

    def get_pins_stats(self):
        """Obtener estadísticas de PINés por tipo de juego"""
        query = """
        SELECT 
            value,
            game_type,
            COUNT(*) as total,
            COUNT(*) as available,
            0 as used
        FROM pins 
        WHERE is_used = false
        GROUP BY value, game_type
        ORDER BY game_type, value ASC
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

    # Función de verificación de disponibilidad removida por solicitud del usuario

    def get_freefire_latam_pin(self, amount_value):
        """FUNCIÓN EXCLUSIVA para Free Fire Latam - NO reutilizar para otros juegos"""
        import requests
        import os

        # Credenciales específicas para Free Fire Latam
        provider_user = os.getenv('FREEFIRE_LATAM_USER')
        provider_password = os.getenv('FREEFIRE_LATAM_PASSWORD')
        api_url = "https://inefableshop.net/conexion_api/api.php"

        print(f"[FREEFIRE LATAM] Verificando credenciales...")
        print(f"[FREEFIRE LATAM] Usuario configurado: {'Sí' if provider_user else 'NO'}")
        print(f"[FREEFIRE LATAM] Contraseña configurada: {'Sí' if provider_password else 'NO'}")

        if not provider_user or not provider_password:
            print("[FREEFIRE LATAM] ❌ Error: Credenciales no configuradas en variables de entorno")
            print("[FREEFIRE LATAM] Verifica FREEFIRE_LATAM_USER y FREEFIRE_LATAM_PASSWORD")
            return None

        # Validar valores específicos de Free Fire Latam (1-9)
        if amount_value < 1 or amount_value > 9:
            print(f"[FREEFIRE LATAM] ❌ Valor {amount_value} inválido. Debe estar entre 1-9")
            return None

        # Parámetros específicos para Free Fire Latam
        params = {
            'action': 'recarga',
            'usuario': provider_user,
            'clave': provider_password,
            'tipo': 'recargaPinFreefirebs',  # Tipo específico para Free Fire Latam
            'monto': str(amount_value),
            'numero': '0'
        }

        try:
            print(f"[FREEFIRE LATAM] 🚀 Consultando API con parámetros: {params}")
            print(f"[FREEFIRE LATAM] 🌐 URL: {api_url}")
            
            response = requests.get(api_url, params=params, timeout=30)
            print(f"[FREEFIRE LATAM] 📡 Código de respuesta HTTP: {response.status_code}")
            
            response.raise_for_status()
            response_data = response.text.strip()
            print(f"[FREEFIRE LATAM] 📄 Respuesta completa: {response_data}")

            if not response_data:
                print("[FREEFIRE LATAM] ❌ Respuesta vacía de la API")
                return None

            # Procesamiento específico para Free Fire Latam
            try:
                import json
                json_response = json.loads(response_data)
                print(f"[FREEFIRE LATAM] 📋 JSON parseado exitosamente: {json_response}")
                return self._process_freefire_latam_response(json_response, amount_value)
            except json.JSONDecodeError as json_error:
                print(f"[FREEFIRE LATAM] ⚠️  Error JSON, intentando procesar con warnings: {json_error}")
                return self._process_freefire_latam_warnings_response(response_data, amount_value)

        except requests.exceptions.Timeout:
            print("[FREEFIRE LATAM] ❌ Timeout: La API tardó más de 30 segundos en responder")
            return None
        except requests.exceptions.ConnectionError:
            print("[FREEFIRE LATAM] ❌ Error de conexión: No se puede conectar con la API")
            return None
        except requests.exceptions.HTTPError as http_error:
            print(f"[FREEFIRE LATAM] ❌ Error HTTP: {http_error}")
            return None
        except Exception as e:
            print(f"[FREEFIRE LATAM] ❌ Error inesperado: {type(e).__name__}: {e}")
            return None

    def _process_freefire_latam_response(self, json_response, amount_value):
        """Procesar respuesta JSON específica de Free Fire Latam"""
        alert_status = json_response.get('ALERTA') or json_response.get('alerta', '').upper()
        pin_code = json_response.get('PIN') or json_response.get('pin')

        # Extraer PIN del mensaje si es necesario
        if not pin_code and 'mensaje' in json_response:
            import re
            pin_match = re.search(r'<b>Pin:<\/b>\s*([A-Z0-9]+)', json_response['mensaje'])
            if pin_match:
                pin_code = pin_match.group(1).strip()

        if (alert_status == 'VERDE' or alert_status == 'GREEN') and pin_code:
            pin_code = pin_code.upper().strip()
            if 4 <= len(pin_code) <= 20:
                return {
                    'pin_code': pin_code,
                    'value': amount_value,
                    'source': 'freefire_latam_api'
                }

        error_msg = json_response.get('MENSAJE', 'Error desconocido')
        print(f"[FREEFIRE LATAM] Error de API: {error_msg}")
        return None

    def _process_freefire_latam_warnings_response(self, response_data, amount_value):
        """Procesar respuesta con warnings PHP específica de Free Fire Latam"""
        try:
            import json
            json_start = response_data.find('{')
            if json_start != -1:
                json_part = response_data[json_start:]
                json_response = json.loads(json_part)
                return self._process_freefire_latam_response(json_response, amount_value)
        except:
            pass

        print(f"[FREEFIRE LATAM] No se pudo procesar respuesta: {response_data}")
        return None



    def get_freefire_global_pin(self, amount_value):
        """FUNCIÓN EXCLUSIVA para Free Fire Global - Completamente independiente"""
        # TODO: Implementar cuando se configure Free Fire Global
        print(f"[FREEFIRE GLOBAL] Función no implementada aún")
        return None

    def get_block_striker_pin(self, amount_value):
        """FUNCIÓN EXCLUSIVA para Block Striker - Completamente independiente"""
        # TODO: Implementar cuando se configure Block Striker
        print(f"[BLOCK STRIKER] Función no implementada aún")
        return None

    def insert_block_striker_transaction(self, user_id, player_id, code, transaction_id, amount, option_value):
        """Insertar transacción específica de Block Striker con player_id y status procesando"""
        query = """
        INSERT INTO transactions (user_id, pin, transaction_id, amount, created_at, player_id, game_type, option_value, status)
        VALUES (%s, %s, %s, %s, NOW(), %s, %s, %s, %s)
        RETURNING *
        """
        result = self.execute_query(query, (user_id, code, transaction_id, amount, player_id, 'Block Striker', option_value, 'procesando'))

        # Limpiar transacciones antiguas después de insertar una nueva
        if result:
            self.cleanup_old_transactions(user_id)

        return result

    def update_block_striker_transaction_status(self, transaction_id, new_status):
        """Actualizar el status de una transacción de Block Striker"""
        # Primero obtener la transacción para saber el monto y usuario
        get_transaction_query = """
        SELECT user_id, amount FROM transactions 
        WHERE transaction_id = %s AND game_type = 'Block Striker'
        """
        transaction_result = self.execute_query(get_transaction_query, (transaction_id,))

        if not transaction_result:
            return None

        transaction = transaction_result[0]
        user_id = transaction['user_id']
        amount = float(transaction['amount'])

        # Si se rechaza la transacción, devolver el dinero al usuario ANTES de actualizar el status
        if new_status == 'rechazado' and amount < 0:
            # amount es negativo, así que sumamos su valor absoluto para devolver el dinero
            refund_amount = abs(amount)

            # Actualizar el saldo del usuario
            update_balance_query = """
            UPDATE users 
            SET balance = balance + %s 
            WHERE user_id = %s
            """
            balance_result = self.execute_query(update_balance_query, (refund_amount, user_id))

            if balance_result is None:
                print(f"Error devolviendo dinero al usuario {user_id}")
                return None

        # Actualizar el status de la transacción
        update_query = """
        UPDATE transactions 
        SET status = %s 
        WHERE transaction_id = %s AND game_type = 'Block Striker'
        RETURNING *
        """
        result = self.execute_query(update_query, (new_status, transaction_id))

        return result

    def cleanup_old_transactions(self, user_id, max_transactions=20):
        """Eliminar transacciones antiguas manteniendo solo las últimas 20 por usuario"""
        try:
            # Contar transacciones del usuario
            count_query = "SELECT COUNT(*) FROM transactions WHERE user_id = %s"
            count_result = self.execute_query(count_query, (user_id,))

            if count_result and count_result[0]['count'] > max_transactions:
                transactions_to_delete = count_result[0]['count'] - max_transactions

                # Eliminar las transacciones más antiguas que excedan el límite
                delete_query = """
                DELETE FROM transactions 
                WHERE user_id = %s 
                AND id IN (
                    SELECT id FROM (
                        SELECT id FROM transactions 
                        WHERE user_id = %s 
                        ORDER BY created_at ASC 
                        LIMIT %s
                    ) AS old_transactions
                )
                """
                result = self.execute_query(delete_query, (user_id, user_id, transactions_to_delete))

                if result is not None:
                    print(f"[CLEANUP] Eliminadas {transactions_to_delete} transacciones antiguas del usuario {user_id}")
                    return True
                else:
                    print(f"[CLEANUP] Error eliminando transacciones del usuario {user_id}")
                    return False

            return True

        except Exception as e:
            print(f"[CLEANUP] Error en cleanup_old_transactions: {e}")
            return False

    def save_game_prices(self, game_type, prices):
        """Guardar precios de un juego en la base de datos"""
        try:
            # Crear tabla si no existe
            create_table_query = """
            CREATE TABLE IF NOT EXISTS game_prices (
                id SERIAL PRIMARY KEY,
                game_type VARCHAR(50) NOT NULL,
                option_key VARCHAR(10) NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(game_type, option_key)
            )
            """
            self.execute_query(create_table_query)

            # Eliminar precios existentes del juego
            delete_query = "DELETE FROM game_prices WHERE game_type = %s"
            self.execute_query(delete_query, (game_type,))

            # Insertar nuevos precios
            for option_key, price in prices.items():
                insert_query = """
                INSERT INTO game_prices (game_type, option_key, price) 
                VALUES (%s, %s, %s)
                """
                self.execute_query(insert_query, (game_type, str(option_key), float(price)))

            print(f"✅ Precios de {game_type} guardados en base de datos")
            return True

        except Exception as e:
            print(f"❌ Error guardando precios en base de datos: {e}")
            return False

    def load_game_prices(self):
        """Cargar precios de juegos desde la base de datos"""
        try:
            # Crear tabla si no existe
            create_table_query = """
            CREATE TABLE IF NOT EXISTS game_prices (
                id SERIAL PRIMARY KEY,
                game_type VARCHAR(50) NOT NULL,
                option_key VARCHAR(10) NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(game_type, option_key)
            )
            """
            self.execute_query(create_table_query)

            # Cargar precios desde la base de datos
            query = "SELECT game_type, option_key, price FROM game_prices ORDER BY game_type, option_key"
            result = self.execute_query(query)

            prices = {
                "freefire_latam": {},
                "freefire_global": {},
                "block_striker": {}
            }

            if result:
                for row in result:
                    game_type = row['game_type']
                    option_key = row['option_key']
                    price = float(row['price'])

                    if game_type not in prices:
                        prices[game_type] = {}

                    prices[game_type][option_key] = price

            # Verificar que todos los juegos tengan precios configurados
            required_games = ['freefire_latam', 'freefire_global', 'block_striker']
            missing_games = []
            
            for game in required_games:
                if game not in prices or not prices[game]:
                    missing_games.append(game)

            # Si faltan precios de algún juego, agregar valores por defecto
            if not result or not any(prices.values()) or missing_games:
                print(f"📄 Faltan precios para: {missing_games if missing_games else 'todos los juegos'}, creando valores por defecto")
                default_prices = {
                    "freefire_latam": {
                        "1": 0.66, "2": 1.99, "3": 3.35, "4": 6.70, "5": 12.70,
                        "6": 29.50, "7": 0.40, "8": 1.40, "9": 6.50
                    },
                    "freefire_global": {
                        "1": 0.86, "2": 2.90, "3": 4.00, "4": 7.75, "5": 15.30, "6": 38.00
                    },
                    "block_striker": {
                        "1": 0.82, "2": 2.60, "3": 4.30, "4": 8.65, "5": 17.30,
                        "6": 43.15, "7": 3.50, "8": 8.00, "9": 1.85
                    }
                }

                # Guardar solo los precios que faltan
                for game_type in missing_games:
                    if game_type in default_prices:
                        print(f"💾 Guardando precios por defecto para {game_type}")
                        self.save_game_prices(game_type, default_prices[game_type])
                        prices[game_type] = default_prices[game_type]

                # Si no había ningún precio, guardar todos
                if not result or not any(prices.values()):
                    for game_type, game_prices in default_prices.items():
                        self.save_game_prices(game_type, game_prices)
                    return default_prices

            print(f"📄 Precios cargados desde base de datos: {prices}")
            return prices

        except Exception as e:
            print(f"❌ Error cargando precios desde base de datos: {e}")
            # Retornar precios por defecto en caso de error
            return {
                "freefire_latam": {
                    "1": 0.66, "2": 1.99, "3": 3.35, "4": 6.70, "5": 12.70,
                    "6": 29.50, "7": 0.40, "8": 1.40, "9": 6.50
                },
                "freefire_global": {
                    "1": 0.86, "2": 2.90, "3": 4.00, "4": 7.75, "5": 15.30, "6": 38.00
                },
                "block_striker": {
                    "1": 0.82, "2": 2.60, "3": 4.30, "4": 8.65, "5": 17.30,
                    "6": 43.15, "7": 3.50, "8": 8.00, "9": 1.85
                }
            }

    def get_system_config(self, config_key, default_value=None):
        """Obtener una configuración del sistema desde la base de datos"""
        try:
            # Crear tabla si no existe
            create_table_query = """
            CREATE TABLE IF NOT EXISTS system_config (
                id SERIAL PRIMARY KEY,
                config_key VARCHAR(100) UNIQUE NOT NULL,
                config_value TEXT NOT NULL,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            self.execute_query(create_table_query)

            # Obtener configuración
            query = "SELECT config_value FROM system_config WHERE config_key = %s"
            result = self.execute_query(query, (config_key,))

            if result and len(result) > 0:
                return result[0]['config_value']
            elif default_value is not None:
                # Insertar valor por defecto si no existe
                self.set_system_config(config_key, default_value)
                return default_value
            else:
                return None

        except Exception as e:
            print(f"Error obteniendo configuración {config_key}: {e}")
            return default_value

    def set_system_config(self, config_key, config_value, description=None):
        """Establecer una configuración del sistema en la base de datos"""
        try:
            # Crear tabla si no existe
            create_table_query = """
            CREATE TABLE IF NOT EXISTS system_config (
                id SERIAL PRIMARY KEY,
                config_key VARCHAR(100) UNIQUE NOT NULL,
                config_value TEXT NOT NULL,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            self.execute_query(create_table_query)

            # Insertar o actualizar configuración
            upsert_query = """
            INSERT INTO system_config (config_key, config_value, description) 
            VALUES (%s, %s, %s)
            ON CONFLICT (config_key) 
            DO UPDATE SET 
                config_value = EXCLUDED.config_value,
                updated_at = CURRENT_TIMESTAMP
            """
            result = self.execute_query(upsert_query, (config_key, config_value, description))
            return result is not None

        except Exception as e:
            print(f"Error estableciendo configuración {config_key}: {e}")
            return False

    def initialize_default_configs(self):
        """Inicializar configuraciones por defecto del sistema"""
        default_configs = {
            'banner_message': '🎮 ¡Bienvenido a InefableStore! Tu tienda de recargas de juegos más confiable 💎',
            'maintenance_mode': 'false',
            'max_transactions_per_user': '30',
            'freefire_latam_api_enabled': 'true',
            'freefire_global_api_enabled': 'false',
            'block_striker_api_enabled': 'false'
        }

        for key, value in default_configs.items():
            # Solo insertar si no existe
            existing = self.get_system_config(key)
            if existing is None:
                self.set_system_config(key, value, f'Configuración por defecto: {key}')
                print(f"✅ Configuración inicializada: {key} = {value}")

        return True