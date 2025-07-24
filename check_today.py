#!/usr/bin/env python3
from supabase import create_client
import os
from dotenv import load_dotenv
from datetime import datetime
import pandas as pd

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
    print(f"\nCampos disponibles:")
    for col in df.columns:
        print(f"  - {col}")
    
    if 'N° Operación' in df.columns:
        none_count = df['N° Operación'].isna().sum()
        total_count = len(df)
        
        print(f"\n📊 ANÁLISIS:")
        print(f"  Total: {total_count}")
        print(f"  Con N° Operación None: {none_count}")
        print(f"  Con N° Operación válido: {total_count - none_count}")
        print(f"  Porcentaje con None: {(none_count/total_count)*100:.1f}%")
        
        # Mostrar valores únicos
        print(f"\nValores únicos en 'N° Operación':")
        unique_values = df['N° Operación'].unique()
        for val in unique_values:
            count = (df['N° Operación'] == val).sum()
            print(f"  '{val}': {count}")
    else:
        print(f"\n❌ NO EXISTE CAMPO 'N° Operación'")
else:
    print(f"No hay transacciones registradas para hoy") 