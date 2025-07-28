#!/usr/bin/env python3
"""
Script temporal para verificar facturas pendientes para RUT específico
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Buscar facturas pendientes para el RUT específico
print('🔍 Buscando facturas pendientes para RUT 26870197-4:')
response = supabase.table('transferencias').select('*').eq('rut', '26870197-4').eq('enviada', 0).execute()

if response.data:
    print(f'✅ Se encontraron {len(response.data)} facturas pendientes:')
    for factura in response.data:
        print(f'  • Hash: {factura["hash"]}')
        print(f'  • Monto: ${factura["monto"]:,}')
        print(f'  • Fecha: {factura["fecha"]}')
        print(f'  • Empresa: {factura["empresa"]}')
        print(f'  • Facturación: {factura.get("facturación", "N/A")}')
        print(f'  • Enviada: {factura["enviada"]}')
        print('---')
else:
    print('❌ No hay facturas pendientes para este RUT')

# Verificar si está en excepciones
print('\n🔍 Verificando si está en excepciones:')
try:
    excepcion = supabase.table('excepciones_personas_naturales').select('*').eq('rut', '26870197-4').execute()
    if excepcion.data:
        print('✅ RUT encontrado en excepciones:')
        for exc in excepcion.data:
            print(f'  • Activo: {exc["activo"]}')
            print(f'  • Razón Social: {exc["razon_social"]}')
    else:
        print('❌ RUT no encontrado en excepciones')
        print('💡 Necesitas crear la tabla y agregar el RUT')
except Exception as e:
    print(f'⚠️ Error al verificar excepciones: {e}')
    print('💡 La tabla excepciones_personas_naturales no existe aún')

# Verificar datos faltantes
print('\n🔍 Verificando datos faltantes:')
try:
    datos = supabase.table('datos_faltantes').select('*').eq('rut', '26870197-4').execute()
    if datos.data:
        print('✅ Datos encontrados:')
        for dato in datos.data:
            print(f'  • RS: {dato.get("rs", "N/A")}')
            print(f'  • Email: {dato.get("email", "N/A")}')
            print(f'  • Dirección: {dato.get("direccion", "N/A")}')
            print(f'  • Comuna: {dato.get("comuna", "N/A")}')
    else:
        print('❌ No hay datos faltantes para este RUT')
except Exception as e:
    print(f'⚠️ Error al verificar datos faltantes: {e}') 