#!/usr/bin/env python3
"""
Script para actualizar el saldo de BCI con el valor real capturado
Fecha: 2025-07-30
Saldo real: $10,805,314.00
"""

import os
import sys
from datetime import datetime
from supabase import create_client, Client

# Configuración de Supabase
SUPABASE_URL = "https://tmimwpzxmtezopieqzcl.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtaW13cHp4bXRlem9waWVxemNsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzY4NTI5NzQsImV4cCI6MjA1MjQyODk3NH0.tTrdPaiPAkQbF_JlfOOWTQwSs3C_zBbFDZECYzPP-Ho"

def main():
    print("🔄 Actualizando saldo de BCI con el valor real...")
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Conectar a Supabase
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Conectado a Supabase")
        
        # Obtener el último registro
        response = supabase.table('saldo_bancos').select("*").eq('banco', 'BCI').order('fecha_captura', desc=True).limit(1).execute()
        
        if response.data:
            ultimo_registro = response.data[0]
            print(f"📊 Último registro en BD:")
            print(f"   💰 Saldo: ${ultimo_registro['saldo']:,.2f}")
            print(f"   🕐 Fecha: {ultimo_registro['fecha_captura']}")
            
            # Saldo real capturado
            saldo_real = 10805314.00
            diferencia = saldo_real - ultimo_registro['saldo']
            
            print(f"\n🎯 Saldo real capturado: ${saldo_real:,.2f}")
            print(f"📈 Diferencia: ${diferencia:,.2f}")
            
            if abs(diferencia) >= 0.01:
                print(f"✅ Diferencia significativa detectada (${diferencia:,.2f})")
                
                # Insertar nuevo registro con el saldo real
                nuevo_registro = {
                    "banco": "BCI",
                    "saldo": saldo_real,
                    "fecha_captura": datetime.now().isoformat(),
                    "diferencia_anterior": diferencia
                }
                
                insert_response = supabase.table('saldo_bancos').insert(nuevo_registro).execute()
                
                if insert_response.data:
                    print(f"🎉 ¡Saldo actualizado exitosamente!")
                    print(f"   💰 Nuevo saldo: ${saldo_real:,.2f}")
                    print(f"   📈 Diferencia registrada: ${diferencia:,.2f}")
                else:
                    print(f"❌ Error al insertar: {insert_response}")
            else:
                print(f"ℹ️ No hay diferencia significativa")
                
        else:
            print("❌ No se encontraron registros de BCI")
            
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