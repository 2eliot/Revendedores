# Simplificando el sistema de administrador para usar solo 'admin' y 'password'.
from flask import Flask, render_template, session, redirect, url_for, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from database import Database
import os
from dotenv import load_dotenv
from functools import wraps

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'clave_por_defecto')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('auth'))

@app.route('/auth')
def auth():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('auth.html')

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"error": "Email y contraseña son requeridos"}), 400

        # Verificar credenciales del admin desde secretos
        admin_user = os.getenv('ADMIN_USER', 'admin')
        admin_password = os.getenv('ADMIN_PASSWORD', 'password')

        if email == admin_user and password == admin_password:
            session['user_id'] = 'ADMIN001'
            session['nombre'] = 'Admin'
            session['apellido'] = 'Usuario'
            session['email'] = admin_user
            session['telefono'] = '000000000'
            return jsonify({"success": True})
        
        # Si no es admin, verificar en base de datos
        db = Database()
        if not db.connect():
            return jsonify({"error": "Error de conexión a la base de datos"}), 500

        try:
            user = db.get_user_by_email(email)

            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['user_id']
                session['nombre'] = user['nombre']
                session['apellido'] = user['apellido']
                session['email'] = user['email']
                session['telefono'] = user['telefono']
                return jsonify({"success": True})
            else:
                return jsonify({"error": "Email o contraseña incorrectos"}), 401

        finally:
            db.disconnect()

    except Exception as e:
        print(f"Error en login: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@app.route('/register', methods=['POST'])
def register():
    db = Database()
    if not db.connect():
        return jsonify({"error": "Error de conexión a la base de datos"}), 500

    try:
        data = request.get_json()
        nombre = data.get('nombre')
        apellido = data.get('apellido')
        telefono = data.get('telefono')
        email = data.get('email')
        password = data.get('password')

        if not all([nombre, apellido, telefono, email, password]):
            return jsonify({"error": "Todos los campos son requeridos"}), 400

        if len(password) < 6:
            return jsonify({"error": "La contraseña debe tener al menos 6 caracteres"}), 400

        # Verificar si el email ya existe
        existing_user = db.get_user_by_email(email)
        if existing_user:
            return jsonify({"error": "El email ya está registrado"}), 400

        # Crear hash de la contraseña
        password_hash = generate_password_hash(password)

        # Crear usuario
        result = db.create_user(nombre, apellido, telefono, email, password_hash)

        if result:
            return jsonify({"success": True, "message": "Usuario registrado exitosamente"})
        else:
            return jsonify({"error": "No se pudo crear el usuario"}), 500

    except Exception as e:
        print(f"Error en registro: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

    finally:
        db.disconnect()

@app.route('/dashboard')
@login_required
def dashboard():
    db = Database()
    if not db.connect():
        return "Error de conexión a la base de datos", 500

    try:
        user_id = session['user_id']

        # Obtener saldo real de la base de datos
        balance = db.get_user_balance(user_id)
        if balance is None:
            balance = "0.00"

        # Obtener transacciones del usuario
        transactions = db.get_user_transactions(user_id, limit=10)
        if transactions is None:
            transactions = []

        return render_template('dashboard.html', 
                             user_id=user_id, 
                             balance=balance,
                             transactions=transactions)

    finally:
        db.disconnect()

@app.route('/freefirelatam')
@login_required
def freefirelatam():
    db = Database()
    if not db.connect():
        return "Error de conexión a la base de datos", 500

    try:
        user_id = session['user_id']

        # Obtener saldo real de la base de datos
        balance = db.get_user_balance(user_id)
        if balance is None:
            balance = "0.00"

        return render_template('freefirelatam.html', 
                             user_id=user_id, 
                             balance=balance)

    finally:
        db.disconnect()

@app.route('/add_transaction', methods=['POST'])
@login_required
def add_transaction():
    db = Database()
    if not db.connect():
        return jsonify({"error": "Error de conexión a la base de datos"}), 500

    try:
        data = request.get_json()
        user_id = session['user_id']
        pin = data.get('pin')
        transaction_id = data.get('transaction_id')
        amount = data.get('amount')

        result = db.insert_transaction(user_id, pin, transaction_id, amount)

        if result:
            return jsonify({"success": True, "transaction": dict(result[0])})
        else:
            return jsonify({"error": "No se pudo insertar la transacción"}), 400

    finally:
        db.disconnect()

@app.route('/update_balance', methods=['POST'])
@login_required
def update_balance():
    db = Database()
    if not db.connect():
        return jsonify({"error": "Error de conexión a la base de datos"}), 500

    try:
        data = request.get_json()
        user_id = session['user_id']
        new_balance = data.get('balance')

        result = db.update_user_balance(user_id, new_balance)

        if result is not None:
            return jsonify({"success": True})
        else:
            return jsonify({"error": "No se pudo actualizar el saldo"}), 400

    finally:
        db.disconnect()

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth'))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session['user_id'] != 'ADMIN001':
            return redirect(url_for('auth'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
@admin_required
def admin_panel():
    db = Database()
    if not db.connect():
        return "Error de conexión a la base de datos", 500

    try:
        users = db.get_all_users()
        pins_stats = db.get_pins_stats()
        return render_template('admin.html', users=users, pins_stats=pins_stats)
    finally:
        db.disconnect()

@app.route('/admin/add-single-pin', methods=['POST'])
@admin_required
def add_single_pin():
    db = Database()
    if not db.connect():
        return jsonify({"error": "Error de conexión a la base de datos"}), 500

    try:
        data = request.get_json()
        pin_code = data.get('pin_code', '').strip().upper()
        value = float(data.get('value', 0))
        
        if not pin_code or value <= 0:
            return jsonify({"error": "PIN y valor son requeridos"}), 400
        
        if len(pin_code) < 4:
            return jsonify({"error": "El PIN debe tener al menos 4 caracteres"}), 400
        
        # Verificar que el PIN no exista ya
        existing_pin = db.get_pin_by_code(pin_code)
        if existing_pin:
            return jsonify({"error": f"El PIN '{pin_code}' ya existe"}), 400
        
        # Crear el PIN
        result = db.create_pin(pin_code, value)
        
        if result:
            return jsonify({
                "success": True, 
                "message": f"PIN '{pin_code}' de ${value} creado exitosamente"
            })
        else:
            return jsonify({"error": "No se pudo crear el PIN"}), 400

    finally:
        db.disconnect()

@app.route('/freefire-latam/validate-recharge', methods=['POST'])
@login_required
def freefire_latam_validate_recharge():
    """ENDPOINT EXCLUSIVO para Free Fire Latam - NO reutilizar"""
    db = Database()
    if not db.connect():
        return jsonify({"error": "Error de conexión a la base de datos"}), 500

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Datos de solicitud inválidos"}), 400
            
        user_id = session['user_id']
        option_value = data.get('option_value')  # Valor 1-9 específico de Free Fire Latam
        real_price = data.get('real_price')      # Precio real en USD
        
        if option_value is None or real_price is None:
            return jsonify({"error": "Datos de recarga incompletos"}), 400
            
        option_value = int(option_value)
        real_price = float(real_price)
        
        # Validación específica para Free Fire Latam (1-9)
        if option_value < 1 or option_value > 9:
            return jsonify({"error": "Opción de Free Fire Latam inválida"}), 400
            
        if real_price <= 0:
            return jsonify({"error": "Precio inválido"}), 400
        
        # Verificar saldo del usuario
        current_balance = float(db.get_user_balance(user_id))
        if user_id != 'ADMIN001' and current_balance < real_price:
            return jsonify({
                "error": f"Saldo insuficiente. Tu saldo actual es ${current_balance:.2f} y necesitas ${real_price:.2f}. Recarga tu cuenta primero."
            }), 400
        
        # PASO 1: Buscar PIN local específico para Free Fire Latam
        available_pin = db.get_available_pin_by_value(option_value)
        
        # PASO 2: Si no hay PINs locales, usar proveedor específico de Free Fire Latam
        if not available_pin:
            print(f"[FREEFIRE LATAM] No hay PINs locales de opción {option_value} (${real_price})")
            pin_from_provider = db.get_freefire_latam_pin(option_value)
            
            if not pin_from_provider:
                return jsonify({
                    "error": f"No hay PINés de Free Fire Latam disponibles de ${real_price}. Contacta al administrador."
                }), 400
        
        # Descontar saldo
        if user_id != 'ADMIN001':
            new_balance = current_balance - real_price
            balance_updated = db.update_user_balance(user_id, new_balance)
        else:
            new_balance = current_balance
            balance_updated = True
        
        if balance_updated is None:
            return jsonify({"error": "Error al actualizar el saldo"}), 500
        
        # Procesar según origen del PIN
        if available_pin:
            # PIN local de Free Fire Latam
            used_pin = db.use_pin(available_pin['id'], user_id)
            if used_pin:
                transaction_id = f"FFLATAM-LOCAL-{user_id}-{int(__import__('time').time())}"
                db.insert_transaction(user_id, available_pin['pin_code'], transaction_id, -real_price)
                
                return jsonify({
                    "success": True,
                    "pin": available_pin['pin_code'],
                    "transaction_id": transaction_id,
                    "amount": real_price,
                    "new_balance": f"{new_balance:.2f}",
                    "source": "freefire_latam_local"
                })
            else:
                db.update_user_balance(user_id, current_balance)
                return jsonify({"error": "Error al procesar PIN local"}), 500
                
        elif pin_from_provider:
            # PIN del proveedor específico de Free Fire Latam
            transaction_id = f"FFLATAM-API-{user_id}-{int(__import__('time').time())}"
            db.insert_transaction(user_id, pin_from_provider['pin_code'], transaction_id, -real_price)
            
            return jsonify({
                "success": True,
                "pin": pin_from_provider['pin_code'],
                "transaction_id": transaction_id,
                "amount": real_price,
                "new_balance": f"{new_balance:.2f}",
                "source": "freefire_latam_api"
            })
        
        else:
            db.update_user_balance(user_id, current_balance)
            return jsonify({"error": "Error inesperado en Free Fire Latam"}), 500

    finally:
        db.disconnect()

@app.route('/freefire-global/validate-recharge', methods=['POST'])
@login_required
def freefire_global_validate_recharge():
    """ENDPOINT EXCLUSIVO para Free Fire Global - Completamente independiente"""
    return jsonify({"error": "Free Fire Global no implementado aún"}), 501

@app.route('/block-striker/validate-recharge', methods=['POST'])
@login_required
def block_striker_validate_recharge():
    """ENDPOINT EXCLUSIVO para Block Striker - Completamente independiente"""
    return jsonify({"error": "Block Striker no implementado aún"}), 501

@app.route('/admin/users')
@admin_required
def admin_users():
    db = Database()
    if not db.connect():
        return jsonify({"error": "Error de conexión a la base de datos"}), 500

    try:
        users = db.get_all_users()
        return jsonify({"users": [dict(user) for user in users] if users else []})
    finally:
        db.disconnect()

@app.route('/admin/user/<user_id>/toggle', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    db = Database()
    if not db.connect():
        return jsonify({"error": "Error de conexión a la base de datos"}), 500

    try:
        data = request.get_json()
        action = data.get('action')  # 'activate' o 'deactivate'
        
        result = db.toggle_user_status(user_id, action)
        
        if result:
            return jsonify({"success": True, "message": f"Usuario {action}d exitosamente"})
        else:
            return jsonify({"error": "No se pudo actualizar el estado del usuario"}), 400

    finally:
        db.disconnect()

@app.route('/admin/user/<user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    db = Database()
    if not db.connect():
        return jsonify({"error": "Error de conexión a la base de datos"}), 500

    try:
        data = request.get_json()
        
        result = db.delete_user(user_id)
        
        if result:
            return jsonify({"success": True, "message": "Usuario eliminado exitosamente"})
        else:
            return jsonify({"error": "No se pudo eliminar el usuario"}), 400

    finally:
        db.disconnect()

@app.route('/admin/user/<user_id>/add-credit', methods=['POST'])
@admin_required
def add_credit(user_id):
    db = Database()
    if not db.connect():
        return jsonify({"error": "Error de conexión a la base de datos"}), 500

    try:
        data = request.get_json()
        amount = float(data.get('amount', 0))
        
        if amount <= 0:
            return jsonify({"error": "El monto debe ser mayor a 0"}), 400
        
        result = db.add_credit_to_user(user_id, amount)
        
        if result:
            new_balance = db.get_user_balance(user_id)
            return jsonify({
                "success": True, 
                "message": f"Crédito agregado exitosamente",
                "new_balance": str(new_balance)
            })
        else:
            return jsonify({"error": "No se pudo agregar el crédito"}), 400

    finally:
        db.disconnect()

@app.route('/admin/user/<user_id>/set-balance', methods=['POST'])
@admin_required
def set_balance(user_id):
    db = Database()
    if not db.connect():
        return jsonify({"error": "Error de conexión a la base de datos"}), 500

    try:
        data = request.get_json()
        new_balance = float(data.get('balance', 0))
        
        if new_balance < 0:
            return jsonify({"error": "El saldo no puede ser negativo"}), 400
        
        result = db.update_user_balance(user_id, new_balance)
        
        if result is not None:
            return jsonify({
                "success": True, 
                "message": f"Saldo actualizado exitosamente",
                "new_balance": str(new_balance)
            })
        else:
            return jsonify({"error": "No se pudo actualizar el saldo"}), 400

    finally:
        db.disconnect()

# Las credenciales del admin se leen directamente de las variables de entorno
admin_user = os.getenv('ADMIN_USER', 'admin')
admin_password = os.getenv('ADMIN_PASSWORD', 'password')
print(f"Admin configurado - Usuario: {admin_user}, Password: {admin_password}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)