#!/usr/bin/env python3
"""
Script para verificar la sincronización entre datos locales y el servidor Supabase
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sync_verification.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Configuración de Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL") or "https://tmimwpzxmtezopieqzcl.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtaW13cHp4bXRlem9waWVxemNsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzY4NTI5NzQsImV4cCI6MjA1MjQyODk3NH0.tTrdPaiPAkQbF_JlfOOWTQwSs3C_zBbFDZECYzPP-Ho"

def conectar_supabase():
    """Conectar a Supabase"""
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("✅ Conexión a Supabase establecida")
        return supabase
    except Exception as e:
        logger.error(f"❌ Error al conectar con Supabase: {e}")
        return None

def obtener_estadisticas_servidor(supabase_client):
    """Obtener estadísticas del servidor Supabase"""
    try:
        # Obtener total de registros
        response = supabase_client.table("transferencias").select("id", count="exact").execute()
        total_registros = response.count if hasattr(response, 'count') else 0
        
        # Obtener registros de los últimos 7 días
        fecha_limite = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        response_recientes = supabase_client.table("transferencias").select("id").gte("fecha", fecha_limite).execute()
        registros_recientes = len(response_recientes.data) if response_recientes.data else 0
        
        # Obtener registros por empresa
        response_empresas = supabase_client.table("transferencias").select("empresa").execute()
        empresas = {}
        if response_empresas.data:
            for registro in response_empresas.data:
                empresa = registro.get('empresa', 'Sin empresa')
                empresas[empresa] = empresas.get(empresa, 0) + 1
        
        # Obtener registros pendientes de facturación
        response_pendientes = supabase_client.table("transferencias").select("id").eq("enviada", 0).execute()
        registros_pendientes = len(response_pendientes.data) if response_pendientes.data else 0
        
        return {
            'total_registros': total_registros,
            'registros_recientes': registros_recientes,
            'empresas': empresas,
            'registros_pendientes': registros_pendientes
        }
    except Exception as e:
        logger.error(f"❌ Error al obtener estadísticas del servidor: {e}")
        return None

def verificar_archivos_locales():
    """Verificar archivos locales disponibles"""
    archivos_locales = {}
    
    # Verificar directorio EXCEL_SANTANDER
    excel_dir = "EXCEL_SANTANDER"
    if os.path.exists(excel_dir):
        archivos_excel = [f for f in os.listdir(excel_dir) if f.endswith(('.xlsx', '.xls'))]
        archivos_locales['excel_santander'] = {
            'directorio': excel_dir,
            'archivos': archivos_excel,
            'cantidad': len(archivos_excel)
        }
    
    # Verificar directorio Bancos
    bancos_dir = "Bancos"
    if os.path.exists(bancos_dir):
        archivos_bancos = [f for f in os.listdir(bancos_dir) if f.endswith(('.xlsx', '.xls'))]
        archivos_locales['bancos'] = {
            'directorio': bancos_dir,
            'archivos': archivos_bancos,
            'cantidad': len(archivos_bancos)
        }
    
    # Verificar directorio output
    output_dir = "output"
    if os.path.exists(output_dir):
        archivos_output = [f for f in os.listdir(output_dir) if f.endswith(('.xlsx', '.xls', '.pdf'))]
        archivos_locales['output'] = {
            'directorio': output_dir,
            'archivos': archivos_output,
            'cantidad': len(archivos_output)
        }
    
    return archivos_locales

def verificar_logs():
    """Verificar archivos de log disponibles"""
    logs = {}
    
    # Verificar archivos de log
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
                        'ultima_actualizacion': datetime.fromtimestamp(os.path.getmtime(archivo_log))
                    }
            except Exception as e:
                logs[archivo_log] = {
                    'existe': True,
                    'error_lectura': str(e)
                }
        else:
            logs[archivo_log] = {'existe': False}
    
    return logs

def verificar_ultimas_transacciones(supabase_client, limite=10):
    """Obtener las últimas transacciones del servidor"""
    try:
        response = supabase_client.table("transferencias").select("*").order("fecha_detec", desc=True).limit(limite).execute()
        return response.data if response.data else []
    except Exception as e:
        logger.error(f"❌ Error al obtener últimas transacciones: {e}")
        return []

def generar_reporte_sincronizacion():
    """Generar reporte completo de sincronización"""
    logger.info("🔍 Iniciando verificación de sincronización...")
    
    # Conectar a Supabase
    supabase_client = conectar_supabase()
    if not supabase_client:
        return False
    
    # Obtener estadísticas del servidor
    logger.info("📊 Obteniendo estadísticas del servidor...")
    stats_servidor = obtener_estadisticas_servidor(supabase_client)
    
    # Verificar archivos locales
    logger.info("📁 Verificando archivos locales...")
    archivos_locales = verificar_archivos_locales()
    
    # Verificar logs
    logger.info("📋 Verificando archivos de log...")
    logs = verificar_logs()
    
    # Obtener últimas transacciones
    logger.info("🔄 Obteniendo últimas transacciones...")
    ultimas_transacciones = verificar_ultimas_transacciones(supabase_client)
    
    # Generar reporte
    print("\n" + "="*80)
    print("📊 REPORTE DE SINCRONIZACIÓN - DATOS LOCALES vs SERVIDOR")
    print("="*80)
    
    # Estadísticas del servidor
    if stats_servidor:
        print(f"\n🖥️  ESTADÍSTICAS DEL SERVIDOR (Supabase):")
        print(f"   • Total de registros: {stats_servidor['total_registros']:,}")
        print(f"   • Registros últimos 7 días: {stats_servidor['registros_recientes']:,}")
        print(f"   • Registros pendientes de facturación: {stats_servidor['registros_pendientes']:,}")
        
        if stats_servidor['empresas']:
            print(f"   • Distribución por empresa:")
            for empresa, cantidad in stats_servidor['empresas'].items():
                print(f"     - {empresa}: {cantidad:,} registros")
    
    # Archivos locales
    print(f"\n💻 ARCHIVOS LOCALES:")
    for tipo, info in archivos_locales.items():
        print(f"   • {tipo.upper()}: {info['cantidad']} archivos")
        if info['archivos']:
            for archivo in info['archivos'][:5]:  # Mostrar solo los primeros 5
                print(f"     - {archivo}")
            if len(info['archivos']) > 5:
                print(f"     ... y {len(info['archivos']) - 5} más")
    
    # Logs
    print(f"\n📋 ARCHIVOS DE LOG:")
    for archivo, info in logs.items():
        if info.get('existe'):
            if 'ultima_actualizacion' in info:
                print(f"   • {archivo}: {info['lineas']} líneas, última actualización: {info['ultima_actualizacion'].strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print(f"   • {archivo}: Error al leer")
        else:
            print(f"   • {archivo}: No existe")
    
    # Últimas transacciones
    if ultimas_transacciones:
        print(f"\n🔄 ÚLTIMAS TRANSACCIONES (Servidor):")
        for i, trans in enumerate(ultimas_transacciones[:5], 1):
            fecha = trans.get('fecha', 'N/A')
            monto = trans.get('monto', 0)
            rut = trans.get('rut', 'N/A')
            empresa = trans.get('empresa', 'N/A')
            print(f"   {i}. {fecha} | ${monto:,} | {rut} | {empresa}")
    
    # Recomendaciones
    print(f"\n💡 RECOMENDACIONES:")
    if stats_servidor and stats_servidor['registros_recientes'] == 0:
        print("   ⚠️  No hay registros recientes en el servidor. Verificar si los scripts están funcionando.")
    
    if archivos_locales.get('excel_santander', {}).get('cantidad', 0) == 0:
        print("   ⚠️  No hay archivos Excel de Santander locales. Verificar scraping.")
    
    if archivos_locales.get('bancos', {}).get('cantidad', 0) == 0:
        print("   ⚠️  No hay archivos de bancos locales. Verificar descargas.")
    
    if stats_servidor and stats_servidor['registros_pendientes'] > 0:
        print(f"   ℹ️  Hay {stats_servidor['registros_pendientes']} registros pendientes de facturación.")
    
    print("\n" + "="*80)
    logger.info("✅ Verificación de sincronización completada")
    return True

if __name__ == "__main__":
    generar_reporte_sincronizacion() 