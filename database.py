
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
            # Configuración de la base de datos externa
            self.connection = psycopg2.connect(
                host=os.getenv('DB_HOST'),
                database=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                port=os.getenv('DB_PORT', '5432')
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
