#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import time
import psutil
import logging
from datetime import datetime, timedelta
import os
import sys
from pathlib import Path
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('supervisor_scripts.log'),
        logging.StreamHandler()  # También mostrar en consola
    ]
)

# Obtener el directorio actual
current_dir = Path(__file__).parent.absolute()

# Scripts disponibles
ALL_SCRIPTS = [
    "Scrap_bci.py",
    "Scrap_santander.py",
    "Scrap_santander_cla.py",
    "Scrap_estado.py",
    "Facturador_lioren.py"
]

# Scripts habilitados (modificar esta lista para controlar qué scripts se ejecutan)
ENABLED_SCRIPTS = [
    "Scrap_bci.py",
    "Scrap_santander.py",
    "Scrap_estado.py",
    "Facturador_lioren.py"
]

# Configuración de notificaciones
NOTIFICATIONS_ENABLED = True  # Cambiar a False para desactivar
EMAIL_RECIPIENT = "sergio.plaza.altamirano@gmail.com"  # Email de destino

# Configuración de Gmail API (usando las mismas credenciales que Lioren)
CREDENTIALS_PATH = os.getenv("CREDENTIALS_PATH", "certificado/lioren-446620-e63e8a6e22d4.json")
TOKEN_PATH = os.getenv("TOKEN_PATH", "certificado/token.json")
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

# Estadísticas de ejecución
script_stats = {}  # {script_name: {'start_time': datetime, 'restart_count': 0}}

def check_script(script_name):
    """Verifica si un script está en ejecución."""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'status']):
            try:
                if proc.info['cmdline']:
                    cmdline = ' '.join(proc.info['cmdline'])
                    # Verificar que sea exactamente nuestro script y que esté corriendo
                    if (script_name in cmdline and 
                        'python' in cmdline.lower() and 
                        proc.info['status'] in ['running', 'sleeping']):
                        # Verificar que el proceso no sea zombie o terminado
                        if proc.is_running():
                            logging.debug(f"Script {script_name} encontrado corriendo (PID: {proc.info['pid']})")
                            return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return False
    except Exception as e:
        logging.error(f"Error verificando script {script_name}: {e}")
        return False

def obtener_servicio_gmail():
    """Obtiene el servicio de Gmail usando las credenciales de Lioren."""
    creds = None
    if os.path.exists(TOKEN_PATH):
        logging.info(f"Cargando credenciales existentes de: {TOKEN_PATH}")
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logging.info("Refrescando credenciales Gmail API...")
            creds.refresh(Request())
        else:
            logging.info("No hay credenciales válidas, abriendo flujo OAuth2.")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
            logging.info("Autenticación completada.")
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())
            logging.info(f"Credenciales guardadas en: {TOKEN_PATH}")

    service = build("gmail", "v1", credentials=creds)
    return service

def crear_mensaje_gmail(destinatario, asunto, mensaje):
    """Crea un mensaje MIME para Gmail API."""
    mensaje_mime = MIMEMultipart()
    mensaje_mime["to"] = destinatario
    mensaje_mime["subject"] = asunto
    mensaje_mime.attach(MIMEText(mensaje, "plain", "utf-8"))

    raw = base64.urlsafe_b64encode(mensaje_mime.as_bytes()).decode("utf-8")
    return {"raw": raw}

def enviar_mensaje_gmail(service, user_id, message):
    """Envía un mensaje usando Gmail API."""
    try:
        sent_msg = service.users().messages().send(userId=user_id, body=message).execute()
        logging.info(f"Mensaje enviado. ID: {sent_msg.get('id')}")
        return True
    except Exception as e:
        logging.error(f"Error al enviar correo: {e}")
        return False

def send_notification(subject, message):
    """Envía notificación por email usando Gmail API."""
    if not NOTIFICATIONS_ENABLED:
        return
    
    try:
        service = obtener_servicio_gmail()
        msg = crear_mensaje_gmail(EMAIL_RECIPIENT, f"[SUPERVISOR] {subject}", message)
        exito = enviar_mensaje_gmail(service, "me", msg)
        
        if exito:
            logging.info(f"Notificación enviada: {subject}")
        else:
            logging.error(f"Error enviando notificación: {subject}")
    except Exception as e:
        logging.error(f"Error enviando notificación: {e}")

def restart_script(script_name):
    """Reinicia un script y verifica que se inicie correctamente."""
    try:
        # Actualizar estadísticas
        if script_name not in script_stats:
            script_stats[script_name] = {'start_time': datetime.now(), 'restart_count': 0}
        else:
            script_stats[script_name]['restart_count'] += 1
            script_stats[script_name]['start_time'] = datetime.now()
        
        restart_count = script_stats[script_name]['restart_count']
        logging.info(f"Iniciando {script_name} (intento #{restart_count + 1})")
        
        # Verificar que el archivo existe
        script_path = current_dir / script_name
        if not script_path.exists():
            error_msg = f"El archivo {script_name} no existe en {current_dir}"
            logging.error(error_msg)
            send_notification(f"Error crítico: {script_name}", error_msg)
            return False
        
        # Iniciar el proceso
        try:
            process = subprocess.Popen(
                ["python3", str(script_path)],
                cwd=str(current_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Esperar un momento para verificar que el proceso no falle inmediatamente
            time.sleep(3)
            
            # Verificar si el proceso sigue corriendo
            poll_result = process.poll()
            if poll_result is not None:
                # El proceso terminó inmediatamente
                stdout, stderr = process.communicate()
                error_msg = f"El script {script_name} falló al iniciar.\nCódigo de salida: {poll_result}\nError: {stderr}\nSalida: {stdout}"
                logging.error(error_msg)
                
                # Enviar notificación solo si es el primer fallo o cada 3 fallos
                if restart_count == 0 or restart_count % 3 == 0:
                    send_notification(f"Fallo al iniciar: {script_name}", error_msg)
                return False
            
            # Verificar que el proceso esté realmente corriendo usando check_script
            time.sleep(2)  # Dar tiempo adicional para que el script se establezca
            if check_script(script_name):
                logging.info(f"✅ {script_name} iniciado correctamente (PID: {process.pid})")
                
                # Enviar notificación solo si es el primer reinicio o cada 5 reinicios
                if restart_count == 1 or restart_count % 5 == 0:
                    send_notification(
                        f"Script reiniciado: {script_name}", 
                        f"El script {script_name} ha sido reiniciado exitosamente.\nReinicio #{restart_count}\nPID: {process.pid}"
                    )
                return True
            else:
                error_msg = f"El script {script_name} se inició pero no se detecta en la lista de procesos"
                logging.warning(error_msg)
                return False
                
        except subprocess.SubprocessError as e:
            error_msg = f"Error al ejecutar {script_name}: {e}"
            logging.error(error_msg)
            send_notification(f"Error de ejecución: {script_name}", error_msg)
            return False
            
    except Exception as e:
        error_msg = f"Error crítico al reiniciar {script_name}: {e}"
        logging.error(error_msg)
        send_notification(f"Error crítico: {script_name}", error_msg)
        return False

def cleanup_resources():
    """Limpia recursos no utilizados."""
    try:
        # Obtener lista de scripts en ejecución
        running_scripts = set()
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['cmdline']:
                    cmdline = ' '.join(proc.info['cmdline'])
                    for script in ALL_SCRIPTS:
                        if script in cmdline:
                            running_scripts.add(proc.pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Cerrar navegadores Chrome huérfanos
        chrome_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'ppid']):
            try:
                if proc.info['name'] and ('chrome' in proc.info['name'].lower() or 'chromium' in proc.info['name'].lower()):
                    # Verificar si el proceso está relacionado con nuestros scripts
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'playwright' in cmdline or '--remote-debugging-port' in cmdline:
                        # Verificar si el proceso padre ya no existe o no es uno de nuestros scripts
                        try:
                            parent = psutil.Process(proc.info['ppid'])
                            if parent.pid not in running_scripts:
                                chrome_processes.append(proc)
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            # Si no se puede acceder al proceso padre, asumimos que está huérfano
                            chrome_processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        for proc in chrome_processes:
            try:
                proc.terminate()
                logging.info(f"Proceso de Chrome huérfano terminado: PID {proc.pid}")
            except Exception as e:
                logging.error(f"Error al terminar proceso {proc.pid}: {e}")

        logging.info(f"Recursos limpiados exitosamente. {len(chrome_processes)} procesos de Chrome huérfanos terminados")
    except Exception as e:
        logging.error(f"Error al limpiar recursos: {e}")

def send_daily_report():
    """Envía reporte diario de estadísticas."""
    if not NOTIFICATIONS_ENABLED:
        return
    
    try:
        report = f"""📊 REPORTE DIARIO DEL SUPERVISOR

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Servidor: {os.uname().nodename}

"""
        
        for script_name, stats in script_stats.items():
            uptime = datetime.now() - stats['start_time']
            hours = int(uptime.total_seconds() // 3600)
            minutes = int((uptime.total_seconds() % 3600) // 60)
            
            report += f"🔹 {script_name}:\n"
            report += f"   ⏱️  Tiempo activo: {hours}h {minutes}m\n"
            report += f"   🔄 Reinicios: {stats['restart_count']}\n\n"
        
        if not script_stats:
            report += "No hay estadísticas disponibles.\n"
        
        send_notification("Reporte Diario", report)
    except Exception as e:
        logging.error(f"Error enviando reporte diario: {e}")

def main():
    logging.info("Iniciando supervisor de scripts...")
    logging.info(f"Scripts habilitados: {', '.join(ENABLED_SCRIPTS)}")
    
    # Diccionario para rastrear fallos consecutivos y tiempos de espera
    script_failures = {script: {'consecutive_failures': 0, 'last_attempt': None} for script in ENABLED_SCRIPTS}
    
    # Iniciar todos los scripts habilitados al comienzo
    for script in ENABLED_SCRIPTS:
        if not check_script(script):
            logging.info(f"Iniciando {script} por primera vez")
            success = restart_script(script)
            if not success:
                script_failures[script]['consecutive_failures'] = 1
                script_failures[script]['last_attempt'] = datetime.now()
    
    last_cleanup = datetime.now()
    last_report = datetime.now()
    
    while True:
        try:
            current_time = datetime.now()
            
            # Verificar cada script habilitado
            for script in ENABLED_SCRIPTS:
                if not check_script(script):
                    # Calcular tiempo de espera progresiva basado en fallos consecutivos
                    failures = script_failures[script]['consecutive_failures']
                    last_attempt = script_failures[script]['last_attempt']
                    
                    # Espera progresiva: 1min, 2min, 5min, 10min, 15min, luego 30min
                    wait_times = [60, 120, 300, 600, 900, 1800]  # en segundos
                    wait_time = wait_times[min(failures, len(wait_times) - 1)]
                    
                    # Verificar si ha pasado suficiente tiempo desde el último intento
                    if last_attempt is None or (current_time - last_attempt).total_seconds() >= wait_time:
                        logging.warning(f"{script} no está en ejecución (fallos consecutivos: {failures})")
                        success = restart_script(script)
                        
                        if success:
                            # Reiniciar contador de fallos si el script se inició exitosamente
                            script_failures[script]['consecutive_failures'] = 0
                            script_failures[script]['last_attempt'] = None
                        else:
                            # Incrementar contador de fallos
                            script_failures[script]['consecutive_failures'] += 1
                            script_failures[script]['last_attempt'] = current_time
                            
                            # Log del próximo intento
                            next_wait = wait_times[min(script_failures[script]['consecutive_failures'], len(wait_times) - 1)]
                            next_attempt = current_time + timedelta(seconds=next_wait)
                            logging.info(f"Próximo intento para {script}: {next_attempt.strftime('%H:%M:%S')} (en {next_wait//60} minutos)")
                    else:
                        # Calcular tiempo restante
                        time_since_attempt = (current_time - last_attempt).total_seconds()
                        remaining_time = wait_time - time_since_attempt
                        logging.debug(f"Esperando {remaining_time//60:.0f}m {remaining_time%60:.0f}s antes del próximo intento para {script}")
                else:
                    # El script está corriendo, reiniciar contador de fallos si había alguno
                    if script_failures[script]['consecutive_failures'] > 0:
                        logging.info(f"✅ {script} se recuperó después de {script_failures[script]['consecutive_failures']} fallos")
                        script_failures[script]['consecutive_failures'] = 0
                        script_failures[script]['last_attempt'] = None
            
            # Limpiar recursos cada 5 minutos
            if (current_time - last_cleanup).total_seconds() >= 300:
                cleanup_resources()
                last_cleanup = current_time
            
            # Enviar reporte diario a las 8:00 AM
            if (current_time.hour == 8 and current_time.minute == 0 and 
                (current_time - last_report).total_seconds() >= 3600):
                send_daily_report()
                last_report = current_time
            
            time.sleep(60)  # Verificar cada minuto
            
        except Exception as e:
            logging.error(f"Error en el supervisor: {e}")
            time.sleep(300)  # Esperar 5 minutos en caso de error

if __name__ == "__main__":
    main()