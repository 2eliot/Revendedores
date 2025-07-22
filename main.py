
from flask import Flask, render_template, session, redirect, url_for

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'  # Cambia esto por una clave segura

@app.route('/')
def dashboard():
    # Datos de ejemplo para el dashboard
    if 'usuario' not in session:
        # Datos de ejemplo para demostración
        session['nombre'] = 'Juan'
        session['apellido'] = 'Pérez'
        session['usuario'] = 'juan@example.com'
    
    user_id = "USR001"
    balance = "150.00"
    
    return render_template('dashboard.html', user_id=user_id, balance=balance)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
