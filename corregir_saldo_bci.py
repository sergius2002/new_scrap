#!/usr/bin/env python3
"""
Script para corregir el saldo de BCI
"""

from datetime import datetime

def corregir_saldo_bci():
    """Corrige el saldo de BCI guardando el saldo real"""
    try:
        from saldo_bancos_db import guardar_saldo_bci
        
        print("🔧 === CORRECCIÓN SALDO BCI ===")
        print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Saldo real extraído del Excel
        saldo_real = 8669585.00
        
        print(f"💰 Saldo real a guardar: ${saldo_real:,.2f}")
        print(f"🔄 Guardando con forzar=True...")
        
        # Guardar forzadamente
        resultado = guardar_saldo_bci(saldo_real, forzar=True)
        
        if resultado:
            print(f"✅ Saldo corregido exitosamente: ${saldo_real:,.2f}")
            print(f"📝 Ahora el script podrá detectar cambios futuros correctamente")
        else:
            print(f"❌ Error al corregir el saldo")
        
        print("\n================================")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(f"🔍 Detalles: {traceback.format_exc()}")

if __name__ == "__main__":
    corregir_saldo_bci()