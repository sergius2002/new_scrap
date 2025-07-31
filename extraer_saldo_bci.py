#!/usr/bin/env python3
"""
Script para extraer el saldo actual del Excel de BCI
"""

import pandas as pd
import re
from datetime import datetime
import os

def extraer_saldo_bci_excel():
    """Extrae el saldo del archivo Excel de BCI más reciente"""
    try:
        # Usar ruta relativa al directorio actual del script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        archivo_excel = os.path.join(current_dir, "Bancos", "excel_detallado.xlsx")
        
        print("🔍 === EXTRACCIÓN SALDO BCI DESDE EXCEL ===")
        print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Verificar si existe el archivo
        if not os.path.exists(archivo_excel):
            print(f"❌ Archivo no encontrado: {archivo_excel}")
            return
        
        # Obtener fecha de modificación del archivo
        fecha_mod = datetime.fromtimestamp(os.path.getmtime(archivo_excel))
        print(f"📁 Archivo: {archivo_excel}")
        print(f"📅 Última modificación: {fecha_mod.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Leer el archivo Excel
        print("📖 Leyendo archivo Excel...")
        df = pd.read_excel(archivo_excel)
        
        print(f"📊 Filas encontradas: {len(df)}")
        print(f"📊 Columnas: {list(df.columns)}")
        print()
        
        # Buscar la columna de saldo contable
        if 'Saldo contable' in df.columns and len(df) > 0:
            # Obtener el saldo de la primera fila (K2 en Excel = fila 1 en pandas)
            saldo_celda = df.iloc[0]['Saldo contable']
            
            print(f"💰 Saldo en celda K2: {saldo_celda}")
            print(f"💰 Tipo de dato: {type(saldo_celda)}")
            
            if pd.notna(saldo_celda):
                # Normalizar el saldo
                if isinstance(saldo_celda, (int, float)):
                    saldo_normalizado = float(saldo_celda)
                else:
                    saldo_normalizado = normalizar_saldo(str(saldo_celda))
                
                if saldo_normalizado is not None:
                    print(f"✅ Saldo normalizado: ${saldo_normalizado:,.2f}")
                    
                    # Comparar con BD
                    print("\n🔍 Comparando con Base de Datos:")
                    from saldo_bancos_db import obtener_ultimo_saldo_bci
                    
                    ultimo_bd = obtener_ultimo_saldo_bci()
                    if ultimo_bd:
                        saldo_bd = ultimo_bd['saldo']
                        diferencia = abs(saldo_normalizado - saldo_bd)
                        
                        print(f"   💰 Saldo Excel: ${saldo_normalizado:,.2f}")
                        print(f"   💰 Saldo BD: ${saldo_bd:,.2f}")
                        print(f"   📊 Diferencia: ${diferencia:,.2f}")
                        print(f"   ✅ Diferencia > $0.01: {diferencia >= 0.01}")
                        
                        if diferencia >= 0.01:
                            print(f"\n🚨 HAY DIFERENCIA SIGNIFICATIVA")
                            print(f"   💡 Guardando nuevo saldo automáticamente...")
                            
                            # Guardar automáticamente sin preguntar
                            from saldo_bancos_db import guardar_saldo_bci
                            if guardar_saldo_bci(saldo_normalizado, forzar=True):
                                print(f"✅ Saldo guardado exitosamente: ${saldo_normalizado:,.2f}")
                            else:
                                print(f"❌ Error al guardar el saldo")
                        else:
                            print(f"\n✅ Sin diferencias significativas")
                    else:
                        print(f"   ❌ No hay registros en BD para comparar")
                        
                else:
                    print(f"❌ No se pudo normalizar el saldo: {saldo_celda}")
            else:
                print("❌ La celda K2 está vacía")
        else:
            print("❌ No se encontró la columna 'Saldo contable' o no hay filas")
            print(f"Columnas disponibles: {list(df.columns)}")
        
        print("\n================================")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(f"🔍 Detalles: {traceback.format_exc()}")

def normalizar_saldo(saldo_texto):
    """Normaliza el texto del saldo a un número float"""
    try:
        # Remover símbolos y espacios
        saldo_limpio = re.sub(r'[^\d,\.]', '', saldo_texto)
        
        # Manejar diferentes formatos (123,456.78 vs 123.456,78)
        if ',' in saldo_limpio and '.' in saldo_limpio:
            # Determinar cuál es el separador decimal
            ultima_coma = saldo_limpio.rfind(',')
            ultimo_punto = saldo_limpio.rfind('.')
            
            if ultimo_punto > ultima_coma:
                # Formato 123,456.78
                saldo_limpio = saldo_limpio.replace(',', '')
            else:
                # Formato 123.456,78
                saldo_limpio = saldo_limpio.replace('.', '').replace(',', '.')
        elif ',' in saldo_limpio:
            # Solo comas - podría ser separador de miles o decimal
            partes = saldo_limpio.split(',')
            if len(partes) == 2 and len(partes[1]) == 2:
                # Probablemente decimal (123,45)
                saldo_limpio = saldo_limpio.replace(',', '.')
            else:
                # Probablemente separador de miles
                saldo_limpio = saldo_limpio.replace(',', '')
        
        return float(saldo_limpio)
        
    except Exception as e:
        print(f"Error normalizando saldo '{saldo_texto}': {e}")
        return None

if __name__ == "__main__":
    extraer_saldo_bci_excel()