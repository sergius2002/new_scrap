#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import time
import psutil
import logging
from datetime import datetime
import os
import sys
from pathlib import Path

# Configurar logging
logging.basicConfig(
    filename='supervisor_scripts.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
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
    "Scrap_estado.py",
    "Facturador_lioren.py"
]

def check_script(script_name):
    """Verifica si un script está en ejecución."""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if proc.info['cmdline'] and script_name in ' '.join(proc.info['cmdline']):
            return True
    return False

def restart_script(script_name):
    """Reinicia un script."""
    try:
        logging.info(f"Reiniciando {script_name}")
        # Usar python3 explícitamente y el directorio actual
        subprocess.Popen(
            ["python3", str(current_dir / script_name)],
            cwd=str(current_dir)
        )
        return True
    except Exception as e:
        logging.error(f"Error al reiniciar {script_name}: {e}")
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

def main():
    logging.info("Iniciando supervisor de scripts...")
    logging.info(f"Scripts habilitados: {', '.join(ENABLED_SCRIPTS)}")
    
    # Iniciar todos los scripts habilitados al comienzo
    for script in ENABLED_SCRIPTS:
        if not check_script(script):
            logging.info(f"Iniciando {script} por primera vez")
            restart_script(script)
    
    last_cleanup = datetime.now()
    
    while True:
        try:
            current_time = datetime.now()
            
            # Verificar cada script habilitado
            for script in ENABLED_SCRIPTS:
                if not check_script(script):
                    logging.warning(f"{script} no está en ejecución")
                    restart_script(script)
            
            # Limpiar recursos cada 5 minutos
            if (current_time - last_cleanup).total_seconds() >= 300:
                cleanup_resources()
                last_cleanup = current_time
            
            time.sleep(60)  # Verificar cada minuto
            
        except Exception as e:
            logging.error(f"Error en el supervisor: {e}")
            time.sleep(300)  # Esperar 5 minutos en caso de error

if __name__ == "__main__":
    main() 