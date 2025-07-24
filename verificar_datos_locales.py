#!/usr/bin/env python3
"""
Script para verificar los datos locales disponibles
"""

import os
import sys
import pandas as pd
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def verificar_archivos_excel():
    """Verificar archivos Excel disponibles"""
    archivos = {}
    
    # Verificar directorio EXCEL_SANTANDER
    excel_dir = "EXCEL_SANTANDER"
    if os.path.exists(excel_dir):
        archivos_excel = [f for f in os.listdir(excel_dir) if f.endswith(('.xlsx', '.xls'))]
        archivos['excel_santander'] = {
            'directorio': excel_dir,
            'archivos': archivos_excel,
            'cantidad': len(archivos_excel),
            'detalles': []
        }
        
        # Analizar cada archivo
        for archivo in archivos_excel:
            ruta_completa = os.path.join(excel_dir, archivo)
            try:
                df = pd.read_excel(ruta_completa)
                archivos['excel_santander']['detalles'].append({
                    'archivo': archivo,
                    'filas': len(df),
                    'columnas': len(df.columns),
                    'tamaño': os.path.getsize(ruta_completa),
                    'ultima_modificacion': datetime.fromtimestamp(os.path.getmtime(ruta_completa))
                })
            except Exception as e:
                archivos['excel_santander']['detalles'].append({
                    'archivo': archivo,
                    'error': str(e)
                })
    
    # Verificar directorio Bancos
    bancos_dir = "Bancos"
    if os.path.exists(bancos_dir):
        archivos_bancos = [f for f in os.listdir(bancos_dir) if f.endswith(('.xlsx', '.xls'))]
        archivos['bancos'] = {
            'directorio': bancos_dir,
            'archivos': archivos_bancos,
            'cantidad': len(archivos_bancos),
            'detalles': []
        }
        
        # Analizar cada archivo
        for archivo in archivos_bancos:
            ruta_completa = os.path.join(bancos_dir, archivo)
            try:
                df = pd.read_excel(ruta_completa)
                archivos['bancos']['detalles'].append({
                    'archivo': archivo,
                    'filas': len(df),
                    'columnas': len(df.columns),
                    'tamaño': os.path.getsize(ruta_completa),
                    'ultima_modificacion': datetime.fromtimestamp(os.path.getmtime(ruta_completa))
                })
            except Exception as e:
                archivos['bancos']['detalles'].append({
                    'archivo': archivo,
                    'error': str(e)
                })
    
    return archivos

def verificar_logs():
    """Verificar archivos de log"""
    logs = {}
    
    archivos_log = [
        'supervisor_scripts.log',
        'facturacion.log',
        'logs/scraping.log'
    ]
    
    for archivo_log in archivos_log:
        if os.path.exists(archivo_log):
            try:
                with open(archivo_log, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                    lineas = contenido.split('\n')
                    logs[archivo_log] = {
                        'existe': True,
                        'tamaño': len(contenido),
                        'lineas': len(lineas),
                        'ultima_actualizacion': datetime.fromtimestamp(os.path.getmtime(archivo_log)),
                        'ultimas_lineas': lineas[-5:] if len(lineas) > 5 else lineas
                    }
            except Exception as e:
                logs[archivo_log] = {
                    'existe': True,
                    'error_lectura': str(e)
                }
        else:
            logs[archivo_log] = {'existe': False}
    
    return logs

def verificar_scripts():
    """Verificar scripts disponibles"""
    scripts = {}
    
    archivos_script = [
        'supervisor.py',
        'Scrap_bci.py',
        'Scrap_estado.py',
        'Scrap_santander.py',
        'Facturador_lioren.py',
        'bci.py',
        'estado.py',
        'Santander.py'
    ]
    
    for script in archivos_script:
        if os.path.exists(script):
            stats = os.stat(script)
            scripts[script] = {
                'existe': True,
                'tamaño': stats.st_size,
                'ultima_modificacion': datetime.fromtimestamp(stats.st_mtime),
                'ejecutable': os.access(script, os.X_OK)
            }
        else:
            scripts[script] = {'existe': False}
    
    return scripts

def generar_reporte_local():
    """Generar reporte de datos locales"""
    logger.info("🔍 Iniciando verificación de datos locales...")
    
    # Verificar archivos Excel
    logger.info("📊 Analizando archivos Excel...")
    archivos_excel = verificar_archivos_excel()
    
    # Verificar logs
    logger.info("📋 Analizando archivos de log...")
    logs = verificar_logs()
    
    # Verificar scripts
    logger.info("🔧 Verificando scripts...")
    scripts = verificar_scripts()
    
    # Generar reporte
    print("\n" + "="*80)
    print("📊 REPORTE DE DATOS LOCALES")
    print("="*80)
    
    # Archivos Excel
    print(f"\n📁 ARCHIVOS EXCEL:")
    for tipo, info in archivos_excel.items():
        print(f"   • {tipo.upper()}: {info['cantidad']} archivos")
        if info['detalles']:
            for detalle in info['detalles']:
                if 'error' in detalle:
                    print(f"     ❌ {detalle['archivo']}: Error - {detalle['error']}")
                else:
                    print(f"     ✅ {detalle['archivo']}: {detalle['filas']} filas, {detalle['columnas']} columnas")
                    print(f"        Tamaño: {detalle['tamaño']:,} bytes")
                    print(f"        Última modificación: {detalle['ultima_modificacion'].strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Logs
    print(f"\n📋 ARCHIVOS DE LOG:")
    for archivo, info in logs.items():
        if info.get('existe'):
            if 'ultima_actualizacion' in info:
                print(f"   ✅ {archivo}: {info['lineas']} líneas")
                print(f"      Última actualización: {info['ultima_actualizacion'].strftime('%Y-%m-%d %H:%M:%S')}")
                if info['ultimas_lineas']:
                    print(f"      Últimas líneas:")
                    for linea in info['ultimas_lineas']:
                        if linea.strip():
                            print(f"        {linea.strip()}")
            else:
                print(f"   ⚠️  {archivo}: Error al leer")
        else:
            print(f"   ❌ {archivo}: No existe")
    
    # Scripts
    print(f"\n🔧 SCRIPTS DISPONIBLES:")
    scripts_existentes = [s for s, info in scripts.items() if info.get('existe')]
    scripts_faltantes = [s for s, info in scripts.items() if not info.get('existe')]
    
    print(f"   ✅ Scripts existentes ({len(scripts_existentes)}):")
    for script in scripts_existentes:
        info = scripts[script]
        ejecutable = "✅" if info['ejecutable'] else "❌"
        print(f"      {ejecutable} {script} ({info['tamaño']:,} bytes)")
    
    if scripts_faltantes:
        print(f"   ❌ Scripts faltantes ({len(scripts_faltantes)}):")
        for script in scripts_faltantes:
            print(f"      ❌ {script}")
    
    # Resumen
    print(f"\n📈 RESUMEN:")
    total_excel = sum(info['cantidad'] for info in archivos_excel.values())
    total_logs = sum(1 for info in logs.values() if info.get('existe'))
    total_scripts = len(scripts_existentes)
    
    print(f"   • Archivos Excel: {total_excel}")
    print(f"   • Archivos de log: {total_scripts}")
    print(f"   • Scripts disponibles: {total_scripts}")
    
    # Recomendaciones
    print(f"\n💡 RECOMENDACIONES:")
    if total_excel == 0:
        print("   ⚠️  No hay archivos Excel. Verificar si los scrapers están funcionando.")
    
    if not logs.get('supervisor_scripts.log', {}).get('existe'):
        print("   ⚠️  No hay log del supervisor. Verificar si está ejecutándose.")
    
    if 'supervisor.py' not in scripts_existentes:
        print("   ⚠️  Falta el script supervisor.py")
    
    print("\n" + "="*80)
    logger.info("✅ Verificación de datos locales completada")
    return True

if __name__ == "__main__":
    generar_reporte_local() 