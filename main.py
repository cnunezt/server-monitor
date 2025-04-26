import os
import requests
import time
import subprocess
import threading
from flask import Flask

# CONFIGURACIÓN (RELLENA ESTO)
TELEGRAM_BOT_TOKEN = "8073184813:AAE-uG-8KIEeo9qKovH0ID-_dlxrxaQHbEo"  # Ej: "123456789:ABCdefGhIJKlmNoPQRSTuvwxyz"
CHAT_ID = "5063776756"               # Ej: "5063776756"
SERVER_IP = "187.211.132.100"        # IP o dominio a monitorear
PORT = 80                            # Puerto a verificar (80 para HTTP, 443 para HTTPS)

# Configuración para Replit
os.environ['NO_PROXY'] = 'api.telegram.org'  # Evita problemas de proxy

app = Flask(__name__)

# ================= FUNCIONES PRINCIPALES =================
def verificar_conectividad():
    """Verifica si el servidor está accesible mediante TCP/HTTP"""
    try:
        # Método 1: Conexión TCP directa (sin HTTP)
        with socket.create_connection((SERVER_IP, PORT), timeout=5):
            return True
    except:
        try:
            # Método 2: Petición HTTP/HTTPS
            protocol = 'https' if PORT == 443 else 'http'
            response = requests.get(
                f"{protocol}://{SERVER_IP}:{PORT}", 
                timeout=5,
                verify=False,
                headers={'User-Agent': 'ServerMonitor/1.0'}
            )
            return response.status_code < 500
        except:
            return False

def enviar_mensaje(mensaje):
    """Envía mensajes a Telegram con manejo avanzado de errores"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': CHAT_ID,
            'text': mensaje,
            'parse_mode': 'HTML'
        }

        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return True

    except requests.exceptions.RequestException as e:
        error_type = type(e).__name__
        if isinstance(e, requests.exceptions.HTTPError):
            status = e.response.status_code
            if status == 401:
                print("❌ Token de Telegram inválido")
            elif status == 400:
                print("❌ Chat ID no válido")
        print(f"⚠️ Error al enviar mensaje ({error_type}): {str(e)}")
        return False

# ================= MONITOREO =================
def generar_mensaje_estado(online):
    """Genera mensaje detallado con formato"""
    emoji = "🟢" if online else "🔴"
    status = "EN LÍNEA" if online else "FUERA DE LÍNEA"

    return (
        f"{emoji} <b>Estado del Servidor</b> {emoji}\n"
        f"🖥 <b>Servidor:</b> <code>{SERVER_IP}:{PORT}</code>\n"
        f"📡 <b>Estado:</b> {status}\n"
        f"⏱ <b>Última verificación:</b> {time.ctime()}\n"
        f"🔗 <b>Método:</b> {'HTTP' if PORT in (80,443) else 'TCP'}"
    )

def monitor():
    """Monitorea el servidor en segundo plano"""
    print("🚀 Iniciando monitor de servidor...")
    estado_anterior = None

    while True:
        online = verificar_conectividad()

        # Solo notificar si cambió el estado
        if estado_anterior is None or online != estado_anterior:
            mensaje = generar_mensaje_estado(online)
            if enviar_mensaje(mensaje):
                print(f"📤 Notificado: {'Online' if online else 'Offline'}")
            else:
                print("⚠️ Error al notificar")

        estado_anterior = online
        time.sleep(60)  # Verificar cada 60 segundos

# ================= WEB SERVER (PARA REPLIT) =================
@app.route('/')
def home():
    status = "🟢 EN LÍNEA" if verificar_conectividad() else "🔴 FUERA DE LÍNEA"
    return f"""
    <h1>🛠 Monitor de Servidor</h1>
    <p><b>Estado actual:</b> {status}</p>
    <p><b>Servidor:</b> {SERVER_IP}:{PORT}</p>
    <p><b>Última verificación:</b> {time.ctime()}</p>
    <p><b>Notificaciones:</b> Telegram → {CHAT_ID}</p>
    """

# ================= INICIO =================
if __name__ == '__main__':
    # Verificación inicial
    print("🔍 Probando conectividad inicial...")
    print("Resultado:", "Online" if verificar_conectividad() else "Offline")

    # Iniciar monitor en segundo plano
    threading.Thread(target=monitor, daemon=True).start()

    # Configuración especial para Replit
    import socket  # Import aquí para evitar error en verificar_conectividad()
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)