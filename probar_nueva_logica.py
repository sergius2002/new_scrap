#!/usr/bin/env python3
"""
Script para probar la nueva lógica de guardado de saldos
Simula diferentes escenarios para verificar que funciona correctamente
"""

import os
import sys
from datetime import datetime

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from saldo_bancos_db import SaldoBancosDB

def main():
    print("🧪 PROBANDO NUEVA LÓGICA DE GUARDADO")
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    try:
        # Crear instancia de la clase de base de datos
        db = SaldoBancosDB()
        
        # Mostrar estado actual
        print("\n📊 ESTADO ACTUAL:")
        ultimo = db.obtener_ultimo_saldo("BCI")
        if ultimo:
            print(f"   💰 Último saldo: ${ultimo['saldo']:,.2f}")
            print(f"   🕐 Fecha: {ultimo['fecha_captura']}")
        else:
            print("   ℹ️ No hay saldos previos")
        
        # Simular diferentes saldos para probar la lógica
        saldos_prueba = [
            10805314.00,  # Saldo actual (no debería guardarse - igual al último)
            10805314.50,  # Cambio pequeño (debería guardarse)
            10900000.00,  # Cambio grande (debería guardarse)
            10900000.00,  # Mismo saldo (no debería guardarse)
        ]
        
        print(f"\n🎯 PROBANDO DIFERENTES SALDOS:")
        
        for i, saldo in enumerate(saldos_prueba, 1):
            print(f"\n--- Prueba {i}: ${saldo:,.2f} ---")
            
            resultado = db.guardar_saldo("BCI", saldo)
            
            if resultado:
                print(f"✅ Saldo guardado exitosamente")
            else:
                print(f"⏭️ Saldo no guardado (sin cambios significativos)")
        
        # Mostrar resumen final
        print(f"\n📊 RESUMEN FINAL:")
        db.mostrar_resumen_banco("BCI")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Pruebas completadas exitosamente")
    else:
        print("\n❌ Pruebas fallaron")
        sys.exit(1)