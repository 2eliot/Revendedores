
"""
Configuración de Gunicorn para producción en Render
"""
import multiprocessing
import os

# Configuración del servidor
bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 120
keepalive = 2

# Configuración de logs
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Configuración de aplicación
preload_app = True
enable_stdio_inheritance = True

# Variables de entorno
raw_env = [
    'RENDER=true',
]

# Configuración de seguridad
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

def when_ready(server):
    """Callback cuando el servidor está listo"""
    print("🚀 Servidor Gunicorn listo en Render")

def worker_int(worker):
    """Callback cuando un worker recibe SIGINT"""
    print(f"👷 Worker {worker.pid} interrumpido")

def pre_fork(server, worker):
    """Callback antes de crear un worker"""
    print(f"👷 Creando worker {worker.age}")

def post_fork(server, worker):
    """Callback después de crear un worker"""
    print(f"👷 Worker {worker.pid} creado exitosamente")
