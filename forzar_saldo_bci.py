#!/usr/bin/env python3
"""
Script para FORZAR la actualización del saldo de BCI
Ignora la regla de "un saldo por día" y guarda el saldo real
"""

import os
import sys
from datetime import datetime

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from saldo_bancos_db import SaldoBancosDB

def main():
    print("🔄 FORZANDO actualización del saldo de BCI...")
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Crear instancia de la clase de base de datos
        db = SaldoBancosDB()
        
        # Mostrar estado actual
        print("\n📊 Estado actual:")
        ultimo = db.obtener_ultimo_saldo("BCI")
        if ultimo:
            print(f"   💰 Saldo en BD: ${ultimo['saldo']:,.2f}")
            print(f"   🕐 Fecha: {ultimo['fecha_captura']}")
        
        # Saldo real capturado por el script
        saldo_real = 10805314.00
        diferencia = saldo_real - ultimo['saldo'] if ultimo else saldo_real
        
        print(f"\n🎯 Saldo real capturado: ${saldo_real:,.2f}")
        print(f"📈 Diferencia: ${diferencia:,.2f}")
        
        # FORZAR el guardado (ignora la regla de "un saldo por día")
        print(f"\n🚀 FORZANDO guardado del nuevo saldo...")
        
        resultado = db.guardar_saldo("BCI", saldo_real, forzar=True)
        
        if resultado:
            print(f"🎉 ¡Saldo actualizado exitosamente!")
            print(f"   💰 Nuevo saldo: ${saldo_real:,.2f}")
            print(f"   📈 Diferencia: ${diferencia:,.2f}")
            
            # Mostrar resumen actualizado
            print(f"\n📊 Resumen actualizado:")
            db.mostrar_resumen_banco("BCI")
        else:
            print(f"❌ Error al forzar la actualización")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Proceso completado exitosamente")
    else:
        print("\n❌ Proceso falló")
        sys.exit(1)