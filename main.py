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
        return render_template('admin.html', users=users)
    finally:
        db.disconnect()

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