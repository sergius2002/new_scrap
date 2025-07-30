#!/usr/bin/env python3
"""
Script de diagnóstico para BCI
Ejecuta: python3 diagnostico_bci.py
"""

import sys
import os
from datetime import datetime

def diagnosticar_bci():
    """Diagnóstico completo del estado de BCI"""
    try:
        from saldo_bancos_db import SaldoBancosDB, obtener_ultimo_saldo_bci
        
        print("🔍 === DIAGNÓSTICO BCI ===")
        print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        db = SaldoBancosDB()
        
        # 1. Verificar conexión
        print("1️⃣ Conexión a base de datos:")
        try:
            ultimo = obtener_ultimo_saldo_bci()
            print("   ✅ Conexión exitosa")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return
        
        # 2. Último registro
        print("\n2️⃣ Último registro:")
        if ultimo:
            print(f"   💰 Saldo: ${ultimo['saldo']:,.2f}")
            print(f"   📅 Fecha: {ultimo['fecha_captura']}")
        else:
            print("   ℹ️ No hay registros")
        
        # 3. Verificar registro de hoy
        print("\n3️⃣ Registro de hoy:")
        existe_hoy = db.verificar_saldo_hoy("BCI")
        print(f"   {'⚠️ SÍ existe' if existe_hoy else '✅ NO existe'}")
        
        # 4. Historial reciente
        print("\n4️⃣ Últimos 5 registros:")
        historial = db.obtener_historial_saldos("BCI", 5)
        if historial:
            for i, reg in enumerate(historial, 1):
                fecha = reg['fecha_captura'][:19]
                print(f"   {i}. ${reg['saldo']:,.2f} - {fecha}")
        else:
            print("   ℹ️ Sin historial")
        
        # 5. Prueba de guardado
        print("\n5️⃣ Prueba de guardado (saldo ficticio):")
        saldo_prueba = 1000000.99  # Saldo de prueba
        try:
            from saldo_bancos_db import guardar_saldo_bci
            resultado = guardar_saldo_bci(saldo_prueba, forzar=True)
            if resultado:
                print(f"   ✅ Guardado exitoso: ${saldo_prueba:,.2f}")
            else:
                print(f"   ❌ No se pudo guardar")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print("\n================================")
        
    except ImportError as e:
        print(f"❌ Error importando módulos: {e}")
        print("💡 Asegúrate de estar en el directorio correcto")
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        print(f"🔍 Detalles: {traceback.format_exc()}")

if __name__ == "__main__":
    diagnosticar_bci()