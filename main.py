# Simplificando el sistema de administrador para usar solo 'admin' y 'password'.
from flask import Flask, render_template, session, redirect, url_for, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from database import Database
import os
from dotenv import load_dotenv
from functools import wraps
from datetime import timedelta
from flask import send_from_directory

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

# Configurar duración de sesión a 3 horas
app.permanent_session_lifetime = timedelta(hours=3)

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
        admin_user = os.getenv('ADMIN_USER')
        admin_password = os.getenv('ADMIN_PASSWORD')

        if email == admin_user and password == admin_password:
            session.permanent = True  # Hacer la sesión permanente
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
                session.permanent = True  # Hacer la sesión permanente
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
        banner_message = get_banner_message()

        return render_template('dashboard.html', 
                             user_id=user_id, 
                             balance=balance,
                             transactions=transactions,
                             banner_message=banner_message)

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

        banner_message = get_banner_message()
        return render_template('freefirelatam.html', 
                             user_id=user_id, 
                             balance=balance,
                             banner_message=banner_message)

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

@app.route('/freefire')
@login_required
def freefire():
    """Página principal de Free Fire Global"""
    db = Database()
    if not db.connect():
        return "Error de conexión a la base de datos", 500

    try:
        user_id = session['user_id']
        balance = db.get_user_balance(user_id)
        if balance is None:
            balance = "0.00"
        banner_message = get_banner_message()

        return render_template('freefire.html', 
                             user_id=user_id, 
                             balance=balance,
                             banner_message=banner_message)
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

        # Obtener precio real desde configuración dinámica
        current_prices = load_game_prices()
        expected_price = current_prices.get('freefire_latam', {}).get(str(option_value))

        if expected_price is None:
            return jsonify({"error": "Precio no configurado para esta opción"}), 400

        # Verificar que el precio enviado coincida con el configurado
        if abs(real_price - expected_price) > 0.01:
            return jsonify({"error": "Precio no coincide con la configuración actual"}), 400

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

        # Descontar saldo (solo para usuarios normales, no para admin)
        if user_id != 'ADMIN001':
            new_balance = current_balance - real_price
            balance_updated = db.update_user_balance(user_id, new_balance)
            if balance_updated is None:
                return jsonify({"error": "Error al actualizar el saldo"}), 500
        else:
            # El admin no necesita saldo, no descontamos nada
            new_balance = current_balance
            balance_updated = True

        # Procesar según origen del PIN
        if available_pin:
            # PIN local de Free Fire Latam
            used_pin = db.use_pin(available_pin['id'], user_id)
            if used_pin:
                transaction_id = f"FF{user_id[-3:]}{int(__import__('time').time()) % 10000}"
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
            transaction_id = f"FF{user_id[-3:]}{int(__import__('time').time()) % 10000}"
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
    """ENDPOINT EXCLUSIVO para Free Fire Global - Consume PINes prioritarios locales"""
    db = Database()
    if not db.connect():
        return jsonify({"error": "Error de conexión a la base de datos"}), 500

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Datos de solicitud inválidos"}), 400

        user_id = session['user_id']
        region = data.get('region')           # 'latam' o 'global'
        option_value = data.get('option_value') # Valor 1-6 específico de Free Fire Global
        real_price = data.get('real_price')     # Precio real en USD

        if not region or region not in ['latam', 'global']:
            return jsonify({"error": "Región inválida"}), 400

        if option_value is None or real_price is None:
            return jsonify({"error": "Datos de recarga incompletos"}), 400

        option_value = int(option_value)
        real_price = float(real_price)

        # Validación específica para Free Fire Global (1-6)
        if option_value < 1 or option_value > 6:
            return jsonify({"error": "Opción de Free Fire Global inválida"}), 400

        # Mapeo de precios fijos para Free Fire Global
        expected_prices = {
            1: 0.86, 2: 2.90, 3: 4.00, 4: 7.75, 5: 15.30, 6: 38.00
        }

        expected_price = expected_prices.get(option_value)
        if expected_price is None:
            return jsonify({"error": "Precio no configurado para esta opción"}), 400

        # Verificar que el precio enviado coincida con el esperado
        if abs(real_price - expected_price) > 0.01:
            return jsonify({"error": "Precio no coincide con la configuración"}), 400

        # Verificar saldo del usuario
        current_balance = float(db.get_user_balance(user_id))
        if user_id != 'ADMIN001' and current_balance < real_price:
            return jsonify({
                "error": f"Saldo insuficiente. Tu saldo actual es ${current_balance:.2f} y necesitas ${real_price:.2f}. Recarga tu cuenta primero."
            }), 400

        # PRIORIDAD 1: Buscar PIN local prioritario por valor
        available_pin = db.get_available_pin_by_value(option_value)

        if available_pin:
            # Descontar saldo (solo para usuarios normales)
            if user_id != 'ADMIN001':
                new_balance = current_balance - real_price
                balance_updated = db.update_user_balance(user_id, new_balance)
                if balance_updated is None:
                    return jsonify({"error": "Error al actualizar el saldo"}), 500
            else:
                new_balance = current_balance

            # Usar PIN local prioritario
            used_pin = db.use_pin(available_pin['id'], user_id)
            if used_pin:
                region_name = "Latam" if region == 'latam' else "Global"
                transaction_id = f"FG{user_id[-3:]}{int(__import__('time').time()) % 10000}"
                
                # Insertar transacción específica de Free Fire Global
                db.insert_freefire_global_transaction(
                    user_id=user_id,
                    pin_code=available_pin['pin_code'],
                    transaction_id=transaction_id,
                    amount=-real_price,
                    region=region,
                    option_value=option_value
                )

                return jsonify({
                    "success": True,
                    "pin": available_pin['pin_code'],
                    "transaction_id": transaction_id,
                    "amount": real_price,
                    "region": region,
                    "new_balance": f"{new_balance:.2f}",
                    "source": "local_pin"
                })
            else:
                # Restaurar saldo si falla el uso del PIN
                if user_id != 'ADMIN001':
                    db.update_user_balance(user_id, current_balance)
                return jsonify({"error": "Error al procesar PIN local"}), 500

        else:
            # Si no hay PINes locales, redirigir según la región
            if region == 'latam':
                # Para Latam, usar API de Free Fire Latam existente
                pin_from_provider = db.get_freefire_latam_pin(option_value)
                
                if pin_from_provider:
                    # Descontar saldo
                    if user_id != 'ADMIN001':
                        new_balance = current_balance - real_price
                        balance_updated = db.update_user_balance(user_id, new_balance)
                        if balance_updated is None:
                            return jsonify({"error": "Error al actualizar el saldo"}), 500
                    else:
                        new_balance = current_balance

                    transaction_id = f"FG{user_id[-3:]}{int(__import__('time').time()) % 10000}"
                    
                    # Insertar transacción
                    db.insert_freefire_global_transaction(
                        user_id=user_id,
                        pin_code=pin_from_provider['pin_code'],
                        transaction_id=transaction_id,
                        amount=-real_price,
                        region=region,
                        option_value=option_value
                    )

                    return jsonify({
                        "success": True,
                        "pin": pin_from_provider['pin_code'],
                        "transaction_id": transaction_id,
                        "amount": real_price,
                        "region": region,
                        "new_balance": f"{new_balance:.2f}",
                        "source": "freefire_latam_api"
                    })
                else:
                    return jsonify({
                        "error": f"No hay PINés disponibles de ${real_price} para Free Fire Latam. Contacta al administrador."
                    }), 400
            else:
                # Para Global, mostrar error ya que no hay API externa configurada
                return jsonify({
                    "error": f"No hay PINés locales disponibles de ${real_price} para Free Fire Global. Contacta al administrador para agregar más PINés."
                }), 400

    finally:
        db.disconnect()

@app.route('/blockstriker')
@login_required
def blockstriker():
    """Página de Block Striker - Independiente de otros juegos"""
    user_id = session.get('user_id')

    db = Database()
    if not db.connect():
        flash('Error de conexión a la base de datos', 'error')
        return redirect(url_for('dashboard'))

    try:
        balance = db.get_user_balance(user_id)
        banner_message = get_banner_message()
        return render_template('blockstriker.html', 
                             user_id=user_id, 
                             balance=balance,
                             banner_message=banner_message)
    finally:
        db.disconnect()

@app.route('/block-striker/validate-recharge', methods=['POST'])
@login_required
def block_striker_validate_recharge():
    """ENDPOINT EXCLUSIVO para Block Striker - Completamente independiente"""
    db = Database()
    if not db.connect():
        return jsonify({"error": "Error de conexión a la base de datos"}), 500

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Datos de solicitud inválidos"}), 400

        user_id = session['user_id']
        player_id = data.get('player_id', '').strip()  # ID del jugador de Block Striker
        option_value = data.get('option_value')  # Valor 1-9 específico de Block Striker
        real_price = data.get('real_price')      # Precio real en USD

        if not player_id:
            return jsonify({"error": "ID del jugador es requerido"}), 400

        if option_value is None or real_price is None:
            return jsonify({"error": "Datos de recarga incompletos"}), 400

        option_value = int(option_value)
        real_price = float(real_price)

        # Validación específica para Block Striker (1-9)
        if option_value < 1 or option_value > 9:
            return jsonify({"error": "Opción de Block Striker inválida"}), 400

        # Obtener precio real desde configuración dinámica
        current_prices = load_game_prices()
        expected_price = current_prices.get('block_striker', {}).get(str(option_value))

        if expected_price is None:
            return jsonify({"error": "Precio no configurado para esta opción"}), 400

        # Verificar que el precio enviado coincida con el configurado
        if abs(real_price - expected_price) > 0.01:
            return jsonify({"error": "Precio no coincide con la configuración actual"}), 400

        if real_price <= 0:
            return jsonify({"error": "Precio inválido"}), 400

        # Verificar saldo del usuario
        current_balance = float(db.get_user_balance(user_id))
        if user_id != 'ADMIN001' and current_balance < real_price:
            return jsonify({
                "error": f"Saldo insuficiente. Tu saldo actual es ${current_balance:.2f} y necesitas ${real_price:.2f}. Recarga tu cuenta primero."
            }), 400

        # Block Striker no requiere código/PIN, solo procesa la compra directamente

        # Descontar saldo (solo para usuarios normales, no para admin)
        if user_id != 'ADMIN001':
            new_balance = current_balance - real_price
            balance_updated = db.update_user_balance(user_id, new_balance)
            if balance_updated is None:
                return jsonify({"error": "Error al actualizar el saldo"}), 500
        else:
            # El admin no necesita saldo, no descontamos nada
            new_balance = current_balance
            balance_updated = True

        # Crear transacción específica para Block Striker sin código
        transaction_id = f"BS{user_id[-3:]}{int(__import__('time').time()) % 10000}"

        # Insertar transacción con información específica de Block Striker (sin código)
        db.insert_block_striker_transaction(
            user_id=user_id,
            player_id=player_id,
            code=None,  # No se genera código para Block Striker
            transaction_id=transaction_id,
            amount=-real_price,
            option_value=option_value
        )

        return jsonify({
            "success": True,
            "player_id": player_id,
            "transaction_id": transaction_id,
            "amount": real_price,
            "new_balance": f"{new_balance:.2f}",
            "source": "block_striker_direct_purchase"
        })

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

@app.route('/admin/block-striker/update-status', methods=['POST'])
@admin_required
def update_block_striker_status():
    """Actualizar el status de una transacción de Block Striker"""
    db = Database()
    if not db.connect():
        return jsonify({"error": "Error de conexión a la base de datos"}), 500

    try:
        data = request.get_json()
        transaction_id = data.get('transaction_id')
        new_status = data.get('status')

        if not transaction_id or not new_status:
            return jsonify({"error": "ID de transacción y status son requeridos"}), 400

        if new_status not in ['procesando', 'aprobado', 'rechazado']:
            return jsonify({"error": "Status inválido"}), 400

        result = db.update_block_striker_transaction_status(transaction_id, new_status)

        if result:
            return jsonify({
                "success": True, 
                "message": f"Transacción {new_status} exitosamente"
            })
        else:
            return jsonify({"error": "No se pudo actualizar el status"}), 400

    finally:
        db.disconnect()

def is_admin():
    """Verifica si el usuario actual tiene rol de administrador."""
    return session.get('user_id') == 'ADMIN001'

@app.route('/admin/update-banner-message', methods=['POST'])
@admin_required
def update_banner_message():
    if not is_admin():
        return jsonify({'success': False, 'error': 'Acceso denegado'}), 403

    try:
        data = request.get_json()
        new_message = data.get('message', '').strip()

        if not new_message:
            return jsonify({'success': False, 'error': 'El mensaje no puede estar vacío'})

        if len(new_message) > 500:
            return jsonify({'success': False, 'error': 'El mensaje es demasiado largo (máximo 500 caracteres)'})

        # Guardar el mensaje en un archivo o variable global
        # Por simplicidad, usaremos un archivo de texto
        with open('banner_message.txt', 'w', encoding='utf-8') as f:
            f.write(new_message)

        return jsonify({'success': True, 'message': 'Mensaje del banner actualizado exitosamente'})

    except Exception as e:
        return jsonify({'success': False, 'error': f'Error al actualizar banner: {str(e)}'})

def get_banner_message():
    """Obtener el mensaje actual del banner"""
    try:
        with open('banner_message.txt', 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        # Mensaje por defecto si no existe el archivo
        return "🚨 IMPORTANTE: GameFan temporalmente fuera de servicio - No comprar PINs hasta nuevo aviso 🚨 Recargas de Block Striker requieren aprobación manual 🚨 Soporte disponible 24/7 para consultas 🚨"

def load_game_prices():
    """Cargar precios de los juegos desde la base de datos"""
    db = Database()
    if not db.connect():
        print("❌ Error conectando a la base de datos para cargar precios")
        # Retornar precios por defecto en caso de error
        return {
            "freefire_latam": {
                "1": 0.66, "2": 1.99, "3": 3.35, "4": 6.70, "5": 12.70,
                "6": 29.50, "7": 0.40, "8": 1.40, "9": 6.50
            },
            "block_striker": {
                "1": 0.82, "2": 2.60, "3": 4.30, "4": 8.65, "5": 17.30,
                "6": 43.15, "7": 3.50, "8": 8.00, "9": 1.85
            }
        }

    try:
        prices = db.load_game_prices()
        return prices
    finally:
        db.disconnect()

def save_game_prices(game_type, prices):
    """Guardar precios de un juego específico en la base de datos"""
    db = Database()
    if not db.connect():
        print("❌ Error conectando a la base de datos para guardar precios")
        return False

    try:
        return db.save_game_prices(game_type, prices)
    finally:
        db.disconnect()

# Endpoint de verificación de disponibilidad removido

@app.route('/admin/get-game-prices')
@login_required
def get_game_prices():
    """Obtener precios actuales de los juegos"""
    try:
        prices = load_game_prices()
        return jsonify({"success": True, "prices": prices})
    except Exception as e:
        return jsonify({"error": f"Error cargando precios: {str(e)}"}), 500

@app.route('/admin/update-game-prices', methods=['POST'])
@admin_required
def update_game_prices():
    """Actualizar precios de un juego específico"""
    try:
        data = request.get_json()
        game_type = data.get('game_type')
        new_prices = data.get('prices')

        print(f"🔄 Actualizando precios de {game_type}: {new_prices}")

        if not game_type or not new_prices:
            return jsonify({"error": "Tipo de juego y precios son requeridos"}), 400

        if game_type not in ['freefire_latam', 'block_striker']:
            return jsonify({"error": "Tipo de juego inválido"}), 400

        # Validar que todos los precios sean números positivos
        for key, price in new_prices.items():
            if not isinstance(price, (int, float)) or price < 0:
                return jsonify({"error": f"Precio inválido para opción {key}"}), 400

        # Convertir precios a formato correcto
        formatted_prices = {}
        for key, price in new_prices.items():
            formatted_prices[str(key)] = float(price)

        print(f"📝 Precios a guardar en base de datos: {formatted_prices}")

        # Guardar precios en la base de datos
        if save_game_prices(game_type, formatted_prices):
            # Verificar que los precios se guardaron correctamente
            saved_prices = load_game_prices()
            if saved_prices.get(game_type) == formatted_prices:
                print(f"✅ Verificación exitosa: Precios de {game_type} persistidos correctamente en base de datos")
                return jsonify({
                    "success": True, 
                    "message": f"Precios de {game_type} actualizados y verificados exitosamente",
                    "saved_prices": saved_prices[game_type]
                })
            else:
                print(f"❌ Error de verificación: Los precios no persistieron correctamente")
                return jsonify({"error": "Error: Los precios no se guardaron correctamente"}), 500
        else:
            return jsonify({"error": "Error guardando precios en base de datos"}), 500

    except Exception as e:
        print(f"❌ Error en update_game_prices: {str(e)}")
        return jsonify({"error": f"Error actualizando precios: {str(e)}"}), 500

# Ruta para servir el service worker
@app.route('/static/service-worker.js')
def service_worker():
    return send_from_directory('static', 'service-worker.js', mimetype='application/javascript')

# Agregar headers de CORS para todas las respuestas
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response

# Las credenciales del admin se leen directamente de las variables de entorno
admin_user = os.getenv('ADMIN_USER')
admin_password = os.getenv('ADMIN_PASSWORD')
print(f"Admin configurado - Usuario: {admin_user if admin_user else 'NO CONFIGURADO'}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)