
from flask import Flask, render_template, session, redirect, url_for, request, jsonify
from database import Database
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'clave_por_defecto')

@app.route('/')
def dashboard():
    db = Database()
    if not db.connect():
        return "Error de conexión a la base de datos", 500
    
    try:
        # Datos de ejemplo para el dashboard
        if 'usuario' not in session:
            session['nombre'] = 'Juan'
            session['apellido'] = 'Pérez'
            session['usuario'] = 'juan@example.com'
        
        user_id = "USR001"
        
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
def add_transaction():
    db = Database()
    if not db.connect():
        return jsonify({"error": "Error de conexión a la base de datos"}), 500
    
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'USR001')
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
def update_balance():
    db = Database()
    if not db.connect():
        return jsonify({"error": "Error de conexión a la base de datos"}), 500
    
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'USR001')
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
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
