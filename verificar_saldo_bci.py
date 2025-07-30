#!/usr/bin/env python3
"""
Script para verificar el saldo actual de BCI vs BD
"""

import sys
import os
from datetime import datetime

def verificar_saldo_bci():
    """Verifica el saldo actual de BCI vs el registrado en BD"""
    try:
        # Importar funciones necesarias
        from saldo_bancos_db import obtener_ultimo_saldo_bci
        
        print("🔍 === VERIFICACIÓN SALDO BCI ===")
        print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 1. Obtener saldo de BD
        print("1️⃣ Saldo en Base de Datos:")
        ultimo_bd = obtener_ultimo_saldo_bci()
        if ultimo_bd:
            saldo_bd = ultimo_bd['saldo']
            fecha_bd = ultimo_bd['fecha_captura']
            print(f"   💰 Saldo BD: ${saldo_bd:,.2f}")
            print(f"   📅 Fecha: {fecha_bd}")
        else:
            print("   ❌ No hay registros en BD")
            return
        
        # 2. Verificar saldo en memoria (si existe)
        print("\n2️⃣ Saldo en Memoria (Scrap_bci):")
        try:
            # Importar la variable global de Scrap_bci
            import Scrap_bci
            saldos_memoria = Scrap_bci.saldos_memoria
            
            if saldos_memoria["ultimo_saldo"]:
                saldo_memoria = saldos_memoria["ultimo_saldo"]
                fecha_memoria = saldos_memoria["fecha_captura"]
                print(f"   💰 Saldo memoria: ${saldo_memoria:,.2f}")
                print(f"   📅 Fecha: {fecha_memoria}")
                
                # Comparar
                diferencia = abs(saldo_memoria - saldo_bd)
                print(f"\n3️⃣ Comparación:")
                print(f"   📊 Diferencia: ${diferencia:,.2f}")
                print(f"   ✅ Diferencia > $0.01: {diferencia >= 0.01}")
                
                if diferencia >= 0.01:
                    print(f"   🚨 HAY DIFERENCIA SIGNIFICATIVA - Debería guardarse")
                else:
                    print(f"   ✅ Sin diferencias significativas")
                    
            else:
                print("   ℹ️ No hay saldo en memoria")
                
        except ImportError:
            print("   ⚠️ No se puede acceder a la memoria de Scrap_bci")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # 3. Simular captura de saldo actual
        print("\n4️⃣ Simulación de captura:")
        print("   💡 Para verificar el saldo real, ejecuta el script BCI")
        print("   💡 O revisa manualmente el archivo Excel más reciente")
        
        # 4. Verificar archivos Excel recientes
        print("\n5️⃣ Archivos Excel recientes:")
        try:
            import glob
            import os
            
            # Buscar archivos Excel en el directorio actual
            archivos_excel = glob.glob("*.xlsx") + glob.glob("*.xls")
            if archivos_excel:
                # Ordenar por fecha de modificación
                archivos_excel.sort(key=os.path.getmtime, reverse=True)
                print(f"   📁 Archivos encontrados: {len(archivos_excel)}")
                for i, archivo in enumerate(archivos_excel[:3], 1):
                    fecha_mod = datetime.fromtimestamp(os.path.getmtime(archivo))
                    print(f"   {i}. {archivo} - {fecha_mod.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print("   ℹ️ No se encontraron archivos Excel")
                
        except Exception as e:
            print(f"   ❌ Error buscando archivos: {e}")
        
        print("\n================================")
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        print(f"🔍 Detalles: {traceback.format_exc()}")

if __name__ == "__main__":
    verificar_saldo_bci()