#!/usr/bin/env python3
"""
Ejecutor de Scrapers y Lioren
============================

Este script permite ejecutar todos los scrapers y el facturador Lioren por separado.
Cada proceso se ejecuta en su propio subproceso para evitar conflictos.

Uso:
    python ejecutor_scrapers.py [opcion]

Opciones:
    1 - Ejecutar Scrap_bci.py
    2 - Ejecutar Scrap_estado.py  
    3 - Ejecutar Scrap_santander.py
    4 - Ejecutar Facturador_lioren.py
    5 - Ejecutar todos los scrapers (sin Lioren)
    6 - Ejecutar todo (scrapers + Lioren)
    7 - Mostrar estado de procesos
    8 - Detener todos los procesos
"""

import os
import sys
import subprocess
import time
import signal
import json
from datetime import datetime
from pathlib import Path

class ScraperExecutor:
    def __init__(self):
        self.current_dir = Path(__file__).parent.absolute()
        self.processes = {}
        self.log_dir = self.current_dir / "logs"
        self.log_dir.mkdir(exist_ok=True)
        self.status_file = self.current_dir / "scraper_status.json"
        
        # Configuración de scrapers
        self.scrapers = {
            "bci": {
                "script": "Scrap_bci.py",
                "name": "BCI Scraper",
                "description": "Scraper para Banco BCI"
            },
            "estado": {
                "script": "Scrap_estado.py", 
                "name": "Estado Scraper",
                "description": "Scraper para Banco Estado"
            },
            "santander": {
                "script": "Scrap_santander.py",
                "name": "Santander Scraper", 
                "description": "Scraper para Banco Santander"
            },
            "lioren": {
                "script": "Facturador_lioren.py",
                "name": "Facturador Lioren",
                "description": "Sistema de facturación automática"
            }
        }
        
        # Cargar estado previo si existe
        self.load_status()

    def load_status(self):
        """Carga el estado de procesos desde archivo"""
        try:
            if self.status_file.exists():
                with open(self.status_file, 'r') as f:
                    data = json.load(f)
                    # Verificar si los PIDs siguen activos
                    for key, info in data.items():
                        if self.is_process_running(info.get('pid')):
                            self.processes[key] = info
        except Exception as e:
            print(f"⚠️ Error cargando estado: {e}")

    def save_status(self):
        """Guarda el estado actual de procesos"""
        try:
            status_data = {}
            for key, process_info in self.processes.items():
                if process_info.get('process') and process_info['process'].poll() is None:
                    status_data[key] = {
                        'pid': process_info['process'].pid,
                        'started_at': process_info.get('started_at'),
                        'script': process_info.get('script'),
                        'name': process_info.get('name')
                    }
            
            with open(self.status_file, 'w') as f:
                json.dump(status_data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error guardando estado: {e}")

    def is_process_running(self, pid):
        """Verifica si un proceso está ejecutándose"""
        if not pid:
            return False
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def start_scraper(self, scraper_key):
        """Inicia un scraper específico"""
        if scraper_key not in self.scrapers:
            print(f"❌ Scraper '{scraper_key}' no encontrado")
            return False

        if scraper_key in self.processes and self.processes[scraper_key].get('process'):
            if self.processes[scraper_key]['process'].poll() is None:
                print(f"⚠️ {self.scrapers[scraper_key]['name']} ya está ejecutándose")
                return False

        scraper_info = self.scrapers[scraper_key]
        script_path = self.current_dir / scraper_info['script']
        
        if not script_path.exists():
            print(f"❌ Script no encontrado: {script_path}")
            return False

        # Crear archivo de log
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"{scraper_key}_{timestamp}.log"
        
        try:
            print(f"🚀 Iniciando {scraper_info['name']}...")
            
            # Abrir archivo de log
            log_handle = open(log_file, 'w')
            
            # Iniciar proceso
            process = subprocess.Popen(
                [sys.executable, str(script_path)],
                cwd=str(self.current_dir),
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            # Guardar información del proceso
            self.processes[scraper_key] = {
                'process': process,
                'log_file': str(log_file),
                'log_handle': log_handle,
                'started_at': datetime.now().isoformat(),
                'script': scraper_info['script'],
                'name': scraper_info['name']
            }
            
            print(f"✅ {scraper_info['name']} iniciado (PID: {process.pid})")
            print(f"📝 Log: {log_file}")
            
            self.save_status()
            return True
            
        except Exception as e:
            print(f"❌ Error iniciando {scraper_info['name']}: {e}")
            return False

    def stop_scraper(self, scraper_key):
        """Detiene un scraper específico"""
        if scraper_key not in self.processes:
            print(f"⚠️ {scraper_key} no está ejecutándose")
            return False

        process_info = self.processes[scraper_key]
        process = process_info.get('process')
        
        if not process or process.poll() is not None:
            print(f"⚠️ {scraper_key} no está ejecutándose")
            del self.processes[scraper_key]
            return False

        try:
            print(f"🛑 Deteniendo {process_info.get('name', scraper_key)}...")
            
            # Intentar terminación suave
            process.terminate()
            
            # Esperar hasta 10 segundos
            try:
                process.wait(timeout=10)
                print(f"✅ {process_info.get('name', scraper_key)} detenido")
            except subprocess.TimeoutExpired:
                # Forzar terminación
                process.kill()
                process.wait()
                print(f"⚡ {process_info.get('name', scraper_key)} forzado a detenerse")
            
            # Cerrar archivo de log
            if 'log_handle' in process_info:
                process_info['log_handle'].close()
            
            del self.processes[scraper_key]
            self.save_status()
            return True
            
        except Exception as e:
            print(f"❌ Error deteniendo {scraper_key}: {e}")
            return False

    def stop_all(self):
        """Detiene todos los procesos"""
        print("🛑 Deteniendo todos los procesos...")
        
        for scraper_key in list(self.processes.keys()):
            self.stop_scraper(scraper_key)
        
        print("✅ Todos los procesos detenidos")

    def show_status(self):
        """Muestra el estado de todos los procesos"""
        print("\n" + "="*60)
        print("📊 ESTADO DE SCRAPERS Y LIOREN")
        print("="*60)
        
        if not self.processes:
            print("❌ No hay procesos ejecutándose")
            return

        for scraper_key, process_info in self.processes.items():
            process = process_info.get('process')
            name = process_info.get('name', scraper_key)
            started_at = process_info.get('started_at', 'Desconocido')
            log_file = process_info.get('log_file', 'N/A')
            
            if process and process.poll() is None:
                status = "🟢 EJECUTÁNDOSE"
                pid = process.pid
            else:
                status = "🔴 DETENIDO"
                pid = "N/A"
            
            print(f"\n📋 {name}")
            print(f"   Estado: {status}")
            print(f"   PID: {pid}")
            print(f"   Iniciado: {started_at}")
            print(f"   Log: {log_file}")

    def show_menu(self):
        """Muestra el menú principal"""
        print("\n" + "="*60)
        print("🤖 EJECUTOR DE SCRAPERS Y LIOREN")
        print("="*60)
        print("1. 🏦 Ejecutar Scrap_bci.py")
        print("2. 🏛️ Ejecutar Scrap_estado.py")
        print("3. 🏪 Ejecutar Scrap_santander.py")
        print("4. 📄 Ejecutar Facturador_lioren.py")
        print("5. 🚀 Ejecutar todos los scrapers (sin Lioren)")
        print("6. 🌟 Ejecutar todo (scrapers + Lioren)")
        print("7. 📊 Mostrar estado de procesos")
        print("8. 🛑 Detener todos los procesos")
        print("9. ❌ Salir")
        print("="*60)

    def run_interactive(self):
        """Ejecuta el modo interactivo"""
        while True:
            self.show_menu()
            
            try:
                choice = input("\n👉 Selecciona una opción (1-9): ").strip()
                
                if choice == "1":
                    self.start_scraper("bci")
                elif choice == "2":
                    self.start_scraper("estado")
                elif choice == "3":
                    self.start_scraper("santander")
                elif choice == "4":
                    self.start_scraper("lioren")
                elif choice == "5":
                    print("🚀 Iniciando todos los scrapers...")
                    self.start_scraper("bci")
                    time.sleep(2)
                    self.start_scraper("estado")
                    time.sleep(2)
                    self.start_scraper("santander")
                elif choice == "6":
                    print("🌟 Iniciando todo (scrapers + Lioren)...")
                    self.start_scraper("bci")
                    time.sleep(2)
                    self.start_scraper("estado")
                    time.sleep(2)
                    self.start_scraper("santander")
                    time.sleep(2)
                    self.start_scraper("lioren")
                elif choice == "7":
                    self.show_status()
                elif choice == "8":
                    self.stop_all()
                elif choice == "9":
                    print("👋 Saliendo...")
                    self.stop_all()
                    break
                else:
                    print("❌ Opción inválida. Por favor selecciona 1-9.")
                
                if choice in ["1", "2", "3", "4", "5", "6"]:
                    input("\n⏸️ Presiona Enter para continuar...")
                    
            except KeyboardInterrupt:
                print("\n\n🛑 Interrupción detectada. Deteniendo procesos...")
                self.stop_all()
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    def run_command_line(self, args):
        """Ejecuta comandos desde línea de comandos"""
        if len(args) < 2:
            self.show_menu()
            return

        option = args[1]
        
        if option == "1":
            self.start_scraper("bci")
        elif option == "2":
            self.start_scraper("estado")
        elif option == "3":
            self.start_scraper("santander")
        elif option == "4":
            self.start_scraper("lioren")
        elif option == "5":
            for scraper in ["bci", "estado", "santander"]:
                self.start_scraper(scraper)
                time.sleep(2)
        elif option == "6":
            for scraper in ["bci", "estado", "santander", "lioren"]:
                self.start_scraper(scraper)
                time.sleep(2)
        elif option == "7":
            self.show_status()
        elif option == "8":
            self.stop_all()
        else:
            print("❌ Opción inválida")
            self.show_menu()

def signal_handler(signum, frame):
    """Maneja señales del sistema"""
    print("\n🛑 Señal de interrupción recibida. Deteniendo procesos...")
    executor.stop_all()
    sys.exit(0)

if __name__ == "__main__":
    # Configurar manejo de señales
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    executor = ScraperExecutor()
    
    if len(sys.argv) > 1:
        # Modo línea de comandos
        executor.run_command_line(sys.argv)
    else:
        # Modo interactivo
        executor.run_interactive()