#!/usr/bin/env python3
import pandas as pd
from supabase import create_client
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Obtener la fecha de hoy
hoy = datetime.now().strftime('%Y-%m-%d')
print(f"Analizando transacciones del día de hoy: {hoy}")

# Obtener registros de hoy
response = supabase.table('transferencias').select('*').eq('fecha', hoy).execute()
df = pd.DataFrame(response.data)

print(f"Total de transacciones de hoy ({hoy}): {len(df)}")

if len(df) > 0:
    # Mostrar campos disponibles
    print(f"\nCampos disponibles en la tabla:")
    for col in df.columns:
        print(f"  - {col}")
    
    # Verificar si hay campo de número de operación
    if 'N° Operación' in df.columns:
        # Contar transacciones con N° Operación None
        none_count = df['N° Operación'].isna().sum()
        total_count = len(df)
        
        print(f"\n📊 ANÁLISIS DE NÚMERO DE OPERACIÓN:")
        print(f"  Total transacciones: {total_count}")
        print(f"  Con N° Operación None: {none_count}")
        print(f"  Con N° Operación válido: {total_count - none_count}")
        print(f"  Porcentaje con None: {(none_count/total_count)*100:.1f}%")
        
        # Mostrar valores únicos
        print(f"\nValores únicos en 'N° Operación':")
        unique_values = df['N° Operación'].unique()
        for val in unique_values:
            count = (df['N° Operación'] == val).sum()
            print(f"  '{val}': {count} transacciones")
            
        # Mostrar algunas transacciones con None
        if none_count > 0:
            print(f"\nPrimeras 3 transacciones con N° Operación None:")
            none_transactions = df[df['N° Operación'].isna()].head(3)
            for idx, row in none_transactions.iterrows():
                print(f"\n  Transacción {idx}:")
                print(f"    Empresa: {row.get('empresa', 'N/A')}")
                print(f"    Monto: {row.get('monto', 'N/A')}")
                print(f"    RUT: {row.get('rut', 'N/A')}")
                print(f"    Hash: {row.get('hash', 'N/A')}")
    else:
        print(f"\n❌ NO EXISTE CAMPO 'N° Operación' en la tabla")
        
        # Verificar otros campos que podrían ser el número de operación
        possible_op_fields = ['op', 'operacion', 'numero_operacion', 'id_operacion', 'transaction_id']
        for field in possible_op_fields:
            if field in df.columns:
                print(f"\nCampo '{field}' encontrado:")
                print(df[field].unique())
else:
    print(f"No hay transacciones registradas para hoy ({hoy})")

# También verificar por empresa
print(f"\n📋 ANÁLISIS POR EMPRESA:")
empresas = df['empresa'].unique() if len(df) > 0 else []
for empresa in empresas:
    empresa_df = df[df['empresa'] == empresa]
    if 'N° Operación' in empresa_df.columns:
        none_count = empresa_df['N° Operación'].isna().sum()
        total_count = len(empresa_df)
        print(f"  {empresa}: {none_count}/{total_count} con N° Operación None ({(none_count/total_count)*100:.1f}%)")

# Mostrar todos los campos disponibles
print(f"\nCampos disponibles en la tabla:")
for col in df.columns:
    print(f"  - {col}")

# Mostrar algunos registros completos
print(f"\nPrimeros 3 registros completos:")
for idx, row in df.head(3).iterrows():
    print(f"\nRegistro {idx + 1}:")
    for col in df.columns:
        print(f"  {col}: {row[col]}")

# Verificar si hay campo de número de operación
if 'N° Operación' in df.columns:
    print(f"\nValores únicos en 'N° Operación':")
    print(df['N° Operación'].unique())
else:
    print(f"\n❌ NO EXISTE CAMPO 'N° Operación' en la tabla")

# Verificar otros campos que podrían ser el número de operación
possible_op_fields = ['op', 'operacion', 'numero_operacion', 'id_operacion', 'transaction_id']
for field in possible_op_fields:
    if field in df.columns:
        print(f"\nCampo '{field}' encontrado:")
        print(df[field].unique())

# Buscar transacciones con mismos datos pero hashes diferentes
print("\nBuscando transacciones con mismos datos pero hashes diferentes...")
found_duplicates = False

for idx, row1 in df.iterrows():
    for idx2, row2 in df.iterrows():
        if idx != idx2:
            # Verificar si tienen los mismos datos clave
            if (row1['monto'] == row2['monto'] and 
                row1['rut'] == row2['rut'] and 
                row1['rs'] == row2['rs'] and 
                row1['hash'] != row2['hash']):
                
                found_duplicates = True
                print(f"\n🚨 TRANSACCIÓN DUPLICADA ENCONTRADA:")
                print(f"  Hash 1: {row1['hash']}")
                print(f"  Hash 2: {row2['hash']}")
                print(f"  Monto: {row1['monto']}")
                print(f"  RUT: {row1['rut']}")
                print(f"  RS: {row1['rs']}")
                print(f"  Fecha: {row1['fecha']}")
                print(f"  ID 1: {row1['id']}")
                print(f"  ID 2: {row2['id']}")
                print("---")

if not found_duplicates:
    print("✅ No se encontraron transacciones duplicadas con hashes diferentes")

# También buscar por número de operación
print(f"\nBuscando por número de operación...")
for idx, row1 in df.iterrows():
    for idx2, row2 in df.iterrows():
        if idx != idx2:
            # Verificar si tienen el mismo número de operación
            if (row1.get('N° Operación') == row2.get('N° Operación') and 
                row1['hash'] != row2['hash']):
                
                print(f"\n🚨 MISMO NÚMERO DE OPERACIÓN CON HASHES DIFERENTES:")
                print(f"  N° Operación: {row1.get('N° Operación')}")
                print(f"  Hash 1: {row1['hash']}")
                print(f"  Hash 2: {row2['hash']}")
                print(f"  Monto 1: {row1['monto']}")
                print(f"  Monto 2: {row2['monto']}")
                print(f"  RUT 1: {row1['rut']}")
                print(f"  RUT 2: {row2['rut']}")
                print("---")

# Verificar si hay hashes duplicados específicamente
if len(df) > df['hash'].nunique():
    print(f"\n=== HASHES DUPLICADOS ENCONTRADOS ===")
    duplicate_hashes = df[df.duplicated(subset=['hash'], keep=False)]
    for hash_val in duplicate_hashes['hash'].unique():
        duplicates = df[df['hash'] == hash_val]
        print(f"\nHash duplicado: {hash_val}")
        for idx, row in duplicates.iterrows():
            print(f"  - ID: {row['id']}, Monto: {row['monto']}, RUT: {row['rut']}, RS: {row['rs']}")
else:
    print("\nNo se encontraron hashes duplicados para el 18-07-2025")

# Verificar si hay hashes duplicados en toda la tabla
all_response = supabase.table('transferencias').select('*').execute()
all_df = pd.DataFrame(all_response.data)

print(f"\n=== ANÁLISIS COMPLETO ===")
print(f"Total registros en BD: {len(all_df)}")
print(f"Hashes únicos: {all_df['hash'].nunique()}")
print(f"Duplicados totales: {len(all_df) - all_df['hash'].nunique()}")

# Encontrar hashes duplicados
duplicate_hashes = all_df[all_df.duplicated(subset=['hash'], keep=False)]
if len(duplicate_hashes) > 0:
    print(f"\nHashes duplicados encontrados:")
    for hash_val in duplicate_hashes['hash'].unique():
        duplicates = all_df[all_df['hash'] == hash_val]
        print(f"\nHash: {hash_val}")
        for idx, row in duplicates.iterrows():
            print(f"  - ID: {row['id']}, Empresa: {row['empresa']}, Fecha: {row['fecha']}, Monto: {row['monto']}") 