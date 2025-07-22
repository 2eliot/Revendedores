
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
            return self.cursor.fetchall()
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
        return self.execute_query(query, (user_id, pin, transaction_id, amount))
    
    def get_user_transactions(self, user_id, limit=10, offset=0):
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
        query = "UPDATE users SET balance = %s WHERE user_id = %s"
        return self.execute_query(query, (new_balance, user_id))
    
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
        """
        result = self.execute_query(query, (amount, user_id))
        return result is not None
