
import re
import time
import random
import json
import os
from datetime import datetime

class MemoryUtils:
    """Utilidades que funcionan solo en memoria sin base de datos"""
    
    # Configuraciones estáticas en memoria
    GAME_OPTIONS = {
        'freefire_latam': {
            '1': {'name': '110 💎 Diamantes', 'default_price': 0.66},
            '2': {'name': '341 💎 Diamantes', 'default_price': 1.99},
            '3': {'name': '572 💎 Diamantes', 'default_price': 3.35},
            '4': {'name': '1.166 💎 Diamantes', 'default_price': 6.70},
            '5': {'name': '2.376 💎 Diamantes', 'default_price': 12.70},
            '6': {'name': '6.138 💎 Diamantes', 'default_price': 29.50},
            '7': {'name': 'Tarjeta Básica', 'default_price': 0.40},
            '8': {'name': 'Tarjeta Semanal', 'default_price': 1.40},
            '9': {'name': 'Tarjeta Mensual', 'default_price': 6.50}
        },
        'freefire_global': {
            '1': {'name': '100+10 💎 Diamantes', 'default_price': 0.86},
            '2': {'name': '310+31 💎 Diamantes', 'default_price': 2.90},
            '3': {'name': '520+52 💎 Diamantes', 'default_price': 4.00},
            '4': {'name': '1.060+106 💎 Diamantes', 'default_price': 7.75},
            '5': {'name': '2.180+218 💎 Diamantes', 'default_price': 15.30},
            '6': {'name': '5.600+560 💎 Diamantes', 'default_price': 38.00}
        },
        'block_striker': {
            '1': {'name': '100+16 🪙 Monedas', 'default_price': 0.82},
            '2': {'name': '300+52 🪙 Monedas', 'default_price': 2.60},
            '3': {'name': '500+94 🪙 Monedas', 'default_price': 4.30},
            '4': {'name': '1,000+210 🪙 Monedas', 'default_price': 8.65},
            '5': {'name': '2,000+440 🪙 Monedas', 'default_price': 17.30},
            '6': {'name': '5,000+1,150 🪙 Monedas', 'default_price': 43.15},
            '7': {'name': '🎫 Pase Básico', 'default_price': 3.50},
            '8': {'name': '🎫 Pase Premium', 'default_price': 8.00},
            '9': {'name': '💎 VIP Mensual', 'default_price': 1.85}
        }
    }

    @staticmethod
    def validate_email(email):
        """Validar formato de email sin consultar BD"""
        if not email or len(email) > 254:
            return False
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_phone(phone):
        """Validar formato de teléfono sin consultar BD"""
        if not phone:
            return False
        
        # Limpiar número (solo dígitos)
        clean_phone = re.sub(r'[^\d]', '', phone)
        
        # Validar longitud (entre 7 y 15 dígitos)
        return 7 <= len(clean_phone) <= 15

    @staticmethod
    def validate_password(password):
        """Validar contraseña sin consultar BD"""
        if not password:
            return False, "La contraseña es requerida"
        
        if len(password) < 6:
            return False, "La contraseña debe tener al menos 6 caracteres"
        
        if len(password) > 128:
            return False, "La contraseña es demasiado larga"
        
        return True, ""

    @staticmethod
    def validate_balance(balance):
        """Validar saldo sin consultar BD"""
        try:
            balance_float = float(balance)
            if balance_float < 0:
                return False, "El saldo no puede ser negativo"
            if balance_float > 999999.99:
                return False, "El saldo es demasiado alto"
            return True, ""
        except (ValueError, TypeError):
            return False, "Formato de saldo inválido"

    @staticmethod
    def generate_transaction_id(user_id, prefix="TX"):
        """Generar ID de transacción usando timestamp + random"""
        timestamp = int(time.time())
        random_num = random.randint(1000, 9999)
        user_suffix = user_id[-3:] if len(user_id) >= 3 else user_id
        return f"{prefix}{user_suffix}{timestamp % 100000}{random_num}"

    @staticmethod
    def generate_temp_code(length=8):
        """Generar código temporal aleatorio"""
        chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        return ''.join(random.choice(chars) for _ in range(length))

    @staticmethod
    def calculate_discount(original_price, discount_percent):
        """Calcular descuento sin consultar BD"""
        if discount_percent <= 0:
            return original_price
        
        discount_amount = original_price * (discount_percent / 100)
        final_price = original_price - discount_amount
        return round(final_price, 2)

    @staticmethod
    def calculate_tax(price, tax_percent=0):
        """Calcular impuestos sin consultar BD"""
        if tax_percent <= 0:
            return price
        
        tax_amount = price * (tax_percent / 100)
        return round(price + tax_amount, 2)

    @staticmethod
    def format_currency(amount):
        """Formatear moneda sin consultar BD"""
        try:
            return f"${float(amount):.2f}"
        except (ValueError, TypeError):
            return "$0.00"

    @staticmethod
    def format_datetime(timestamp=None):
        """Formatear fecha y hora sin consultar BD"""
        if timestamp is None:
            dt = datetime.now()
        else:
            dt = datetime.fromtimestamp(timestamp)
        
        return dt.strftime('%d/%m/%Y %H:%M:%S')

    @staticmethod
    def validate_game_option(game_type, option_value):
        """Validar opción de juego sin consultar BD"""
        if game_type not in MemoryUtils.GAME_OPTIONS:
            return False, f"Tipo de juego '{game_type}' no válido"
        
        option_str = str(option_value)
        if option_str not in MemoryUtils.GAME_OPTIONS[game_type]:
            return False, f"Opción {option_value} no válida para {game_type}"
        
        return True, ""

    @staticmethod
    def get_game_option_info(game_type, option_value):
        """Obtener información de opción de juego sin consultar BD"""
        if game_type not in MemoryUtils.GAME_OPTIONS:
            return None
        
        option_str = str(option_value)
        if option_str not in MemoryUtils.GAME_OPTIONS[game_type]:
            return None
        
        return MemoryUtils.GAME_OPTIONS[game_type][option_str]

    @staticmethod
    def validate_price_range(price, min_price=0.01, max_price=1000.00):
        """Validar rango de precios sin consultar BD"""
        try:
            price_float = float(price)
            if price_float < min_price:
                return False, f"El precio mínimo es ${min_price}"
            if price_float > max_price:
                return False, f"El precio máximo es ${max_price}"
            return True, ""
        except (ValueError, TypeError):
            return False, "Formato de precio inválido"

    @staticmethod
    def clean_input(text, max_length=255):
        """Limpiar entrada de texto sin consultar BD"""
        if not text:
            return ""
        
        # Limpiar espacios y caracteres especiales
        cleaned = re.sub(r'[<>"\']', '', str(text).strip())
        
        # Truncar si es necesario
        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length]
        
        return cleaned

    @staticmethod
    def log_error(error_message, error_type="ERROR"):
        """Log de errores a consola sin consultar BD"""
        timestamp = MemoryUtils.format_datetime()
        log_message = f"[{timestamp}] {error_type}: {error_message}"
        print(log_message)
        return log_message

    @staticmethod
    def get_environment_config():
        """Obtener configuraciones desde variables de entorno"""
        return {
            'maintenance_mode': os.getenv('MAINTENANCE_MODE', 'false').lower() == 'true',
            'max_transactions': int(os.getenv('MAX_TRANSACTIONS', '30')),
            'admin_user': os.getenv('ADMIN_USER', 'admin@gmail.com'),
            'freefire_latam_enabled': os.getenv('FREEFIRE_LATAM_ENABLED', 'true').lower() == 'true',
            'freefire_global_enabled': os.getenv('FREEFIRE_GLOBAL_ENABLED', 'true').lower() == 'true',
            'block_striker_enabled': os.getenv('BLOCK_STRIKER_ENABLED', 'true').lower() == 'true'
        }

class PriceCalculator:
    """Calculadora de precios en memoria"""
    
    @staticmethod
    def calculate_bulk_discount(total_amount, bulk_tiers=None):
        """Calcular descuento por volumen sin consultar BD"""
        if bulk_tiers is None:
            bulk_tiers = {
                50.00: 5,   # 5% descuento por compras > $50
                100.00: 10, # 10% descuento por compras > $100
                200.00: 15  # 15% descuento por compras > $200
            }
        
        discount_percent = 0
        for threshold, discount in sorted(bulk_tiers.items(), reverse=True):
            if total_amount >= threshold:
                discount_percent = discount
                break
        
        if discount_percent > 0:
            discount_amount = total_amount * (discount_percent / 100)
            final_price = total_amount - discount_amount
            return {
                'original_price': total_amount,
                'discount_percent': discount_percent,
                'discount_amount': round(discount_amount, 2),
                'final_price': round(final_price, 2)
            }
        
        return {
            'original_price': total_amount,
            'discount_percent': 0,
            'discount_amount': 0,
            'final_price': total_amount
        }

    @staticmethod
    def calculate_processing_fee(amount, fee_percent=2.5):
        """Calcular comisión de procesamiento sin consultar BD"""
        fee_amount = amount * (fee_percent / 100)
        return round(fee_amount, 2)

class ValidationEngine:
    """Motor de validaciones frontend"""
    
    @staticmethod
    def validate_registration_data(data):
        """Validar datos de registro sin consultar BD"""
        errors = []
        
        # Validar nombre
        if not data.get('nombre', '').strip():
            errors.append("El nombre es requerido")
        elif len(data['nombre'].strip()) < 2:
            errors.append("El nombre debe tener al menos 2 caracteres")
        
        # Validar apellido
        if not data.get('apellido', '').strip():
            errors.append("El apellido es requerido")
        elif len(data['apellido'].strip()) < 2:
            errors.append("El apellido debe tener al menos 2 caracteres")
        
        # Validar email
        if not MemoryUtils.validate_email(data.get('email', '')):
            errors.append("Formato de email inválido")
        
        # Validar teléfono
        if not MemoryUtils.validate_phone(data.get('telefono', '')):
            errors.append("Formato de teléfono inválido")
        
        # Validar contraseña
        password_valid, password_error = MemoryUtils.validate_password(data.get('password', ''))
        if not password_valid:
            errors.append(password_error)
        
        return len(errors) == 0, errors

    @staticmethod
    def validate_recharge_data(data, game_type):
        """Validar datos de recarga sin consultar BD"""
        errors = []
        
        # Validar tipo de juego
        game_valid, game_error = MemoryUtils.validate_game_option(
            game_type, data.get('option_value')
        )
        if not game_valid:
            errors.append(game_error)
        
        # Validar precio
        price_valid, price_error = MemoryUtils.validate_price_range(
            data.get('real_price')
        )
        if not price_valid:
            errors.append(price_error)
        
        # Validaciones específicas por juego
        if game_type == 'block_striker':
            if not data.get('player_id', '').strip():
                errors.append("ID del jugador es requerido para Block Striker")
        
        return len(errors) == 0, errors

# Funciones auxiliares globales
def log_to_console(message, level="INFO"):
    """Log simple a consola"""
    return MemoryUtils.log_error(message, level)

def generate_unique_id(prefix="ID"):
    """Generar ID único usando timestamp y random"""
    timestamp = int(time.time())
    random_part = random.randint(100, 999)
    return f"{prefix}{timestamp}{random_part}"
