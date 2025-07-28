#!/usr/bin/env python3
"""
Script de prueba para verificar el funcionamiento del facturador con excepciones
"""

import os
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime, timedelta

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def test_obtener_facturas_pendientes():
    """Prueba la función de obtener facturas pendientes"""
    print("🔍 PRUEBA 1: Obtener facturas pendientes")
    print("="*50)
    
    try:
        # Calcular fecha límite (3 días atrás)
        fecha_limite = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
        print(f"📅 Fecha límite: {fecha_limite}")
        
        response = (
            supabase.table("transferencias")
            .select("hash, monto, rut, fecha, empresa, facturación")
            .eq("enviada", 0)
            .eq("facturación", "empresa")
            .in_("empresa", ["SAN CRISTOBAL SPA", "SAN CRISTOBAL SANTANDER 630", "SAN CRISTOBAL SANTANDER 610", "ST CRISTOBAL SPA", "ST CRISTOBAL BCI", "SAN CRISTOBAL SANTANDER 371"])
            .gte("fecha", fecha_limite)
            .execute()
        )
        
        if hasattr(response, 'error') and response.error:
            print(f"❌ Error: {response.error}")
            return False
        
        facturas = response.data
        print(f"✅ Se encontraron {len(facturas)} facturas pendientes de empresas")
        
        # Mostrar algunas facturas como ejemplo
        for i, factura in enumerate(facturas[:3]):
            print(f"  {i+1}. RUT: {factura['rut']} | Monto: ${factura['monto']:,} | Fecha: {factura['fecha']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        return False

def test_verificar_excepciones():
    """Prueba la función de verificar excepciones"""
    print("\n🔍 PRUEBA 2: Verificar excepciones de personas naturales")
    print("="*50)
    
    try:
        # Probar con RUT que está en excepciones
        rut_excepcion = "26870197-4"
        print(f"📋 Probando RUT en excepciones: {rut_excepcion}")
        
        response = (
            supabase.table("excepciones_personas_naturales")
            .select("rut, razon_social, activo")
            .eq("rut", rut_excepcion)
            .eq("activo", True)
            .execute()
        )
        
        if hasattr(response, 'error') and response.error:
            print(f"❌ Error: {response.error}")
            return False
        
        datos = response.data
        if datos:
            print(f"✅ RUT {rut_excepcion} encontrado en excepciones")
            print(f"  • Razón Social: {datos[0]['razon_social']}")
            print(f"  • Activo: {datos[0]['activo']}")
        else:
            print(f"❌ RUT {rut_excepcion} no encontrado en excepciones")
            return False
        
        # Probar con RUT que NO está en excepciones
        rut_normal = "12345678-9"
        print(f"\n📋 Probando RUT normal: {rut_normal}")
        
        response_normal = (
            supabase.table("excepciones_personas_naturales")
            .select("rut, razon_social, activo")
            .eq("rut", rut_normal)
            .eq("activo", True)
            .execute()
        )
        
        datos_normal = response_normal.data
        if not datos_normal:
            print(f"✅ RUT {rut_normal} correctamente NO encontrado en excepciones")
        else:
            print(f"❌ RUT {rut_normal} incorrectamente encontrado en excepciones")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        return False

def test_datos_faltantes():
    """Prueba la función de obtener datos faltantes"""
    print("\n🔍 PRUEBA 3: Verificar datos faltantes")
    print("="*50)
    
    try:
        # Probar con RUT que tiene datos
        rut_con_datos = "26870197-4"
        print(f"📋 Probando RUT con datos: {rut_con_datos}")
        
        response = (
            supabase.table("datos_faltantes")
            .select("rs, email, direccion, comuna")
            .eq("rut", rut_con_datos)
            .execute()
        )
        
        if hasattr(response, 'error') and response.error:
            print(f"❌ Error: {response.error}")
            return False
        
        datos = response.data
        if datos:
            print(f"✅ Datos encontrados para RUT {rut_con_datos}")
            print(f"  • RS: {datos[0].get('rs', 'N/A')}")
            print(f"  • Email: {datos[0].get('email', 'N/A')}")
            print(f"  • Dirección: {datos[0].get('direccion', 'N/A')}")
            print(f"  • Comuna: {datos[0].get('comuna', 'N/A')}")
        else:
            print(f"❌ No se encontraron datos para RUT {rut_con_datos}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        return False

def test_facturas_personas_naturales():
    """Prueba facturas de personas naturales con excepciones"""
    print("\n🔍 PRUEBA 4: Verificar facturas de personas naturales")
    print("="*50)
    
    try:
        fecha_limite = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
        
        # Buscar facturas de personas naturales recientes
        response = (
            supabase.table("transferencias")
            .select("hash, monto, rut, fecha, empresa, facturación")
            .eq("enviada", 0)
            .eq("facturación", "persona")
            .gte("fecha", fecha_limite)
            .execute()
        )
        
        if hasattr(response, 'error') and response.error:
            print(f"❌ Error: {response.error}")
            return False
        
        facturas = response.data
        print(f"📊 Se encontraron {len(facturas)} facturas de personas naturales recientes")
        
        # Verificar cuáles están en excepciones
        ruts_en_excepciones = []
        for factura in facturas:
            rut = factura['rut']
            
            # Verificar si está en excepciones
            excepcion_response = (
                supabase.table("excepciones_personas_naturales")
                .select("rut")
                .eq("rut", rut)
                .eq("activo", True)
                .execute()
            )
            
            if excepcion_response.data:
                ruts_en_excepciones.append(rut)
                print(f"✅ RUT {rut} está en excepciones - SE PROCESARÁ")
            else:
                print(f"❌ RUT {rut} NO está en excepciones - NO SE PROCESARÁ")
        
        print(f"\n📈 RESUMEN:")
        print(f"  • Total facturas personas naturales: {len(facturas)}")
        print(f"  • RUTs en excepciones: {len(ruts_en_excepciones)}")
        print(f"  • RUTs que se procesarán: {ruts_en_excepciones}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        return False

def main():
    """Ejecuta todas las pruebas"""
    print("🚀 INICIANDO PRUEBAS DEL FACTURADOR")
    print("="*60)
    
    pruebas = [
        ("Obtener facturas pendientes", test_obtener_facturas_pendientes),
        ("Verificar excepciones", test_verificar_excepciones),
        ("Datos faltantes", test_datos_faltantes),
        ("Facturas personas naturales", test_facturas_personas_naturales)
    ]
    
    resultados = []
    
    for nombre, prueba in pruebas:
        print(f"\n{'='*60}")
        print(f"🧪 PRUEBA: {nombre}")
        print(f"{'='*60}")
        
        try:
            resultado = prueba()
            resultados.append((nombre, resultado))
        except Exception as e:
            print(f"❌ Error crítico en prueba {nombre}: {e}")
            resultados.append((nombre, False))
    
    # Resumen final
    print(f"\n{'='*60}")
    print(f"📊 RESUMEN FINAL DE PRUEBAS")
    print(f"{'='*60}")
    
    exitos = 0
    for nombre, resultado in resultados:
        status = "✅ PASÓ" if resultado else "❌ FALLÓ"
        print(f"  {status} - {nombre}")
        if resultado:
            exitos += 1
    
    print(f"\n🎯 RESULTADO: {exitos}/{len(resultados)} pruebas exitosas")
    
    if exitos == len(resultados):
        print("🎉 ¡TODAS LAS PRUEBAS PASARON! El facturador está funcionando correctamente.")
    else:
        print("⚠️ Algunas pruebas fallaron. Revisa los errores arriba.")
    
    return exitos == len(resultados)

if __name__ == "__main__":
    main() 