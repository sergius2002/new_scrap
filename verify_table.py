#!/usr/bin/env python3
"""
Script mejorado para crear la tabla saldo_bancos en Supabase
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase import create_client
from config import SUPABASE_CONFIG
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def verify_and_create_table():
    """Verifica si la tabla existe y la crea si es necesario"""
    try:
        # Conectar a Supabase
        supabase = create_client(
            SUPABASE_CONFIG["url"],
            SUPABASE_CONFIG["key"]
        )
        
        logger.info("🔍 Verificando si la tabla saldo_bancos existe...")
        
        # Intentar hacer una consulta simple para verificar si la tabla existe
        try:
            result = supabase.table('saldo_bancos').select('*').limit(1).execute()
            logger.info("✅ La tabla saldo_bancos ya existe!")
            logger.info(f"📊 Estructura de la tabla verificada. Registros encontrados: {len(result.data)}")
            return True
            
        except Exception as table_error:
            if "relation" in str(table_error).lower() and "does not exist" in str(table_error).lower():
                logger.info("❌ La tabla saldo_bancos no existe. Necesita ser creada manualmente.")
                logger.info("📋 Por favor, ejecuta el siguiente SQL en el dashboard de Supabase:")
                logger.info("=" * 60)
                
                sql_script = """
-- Script SQL simplificado para crear la tabla saldo_bancos en Supabase
-- Ejecutar este script en el SQL Editor de Supabase

CREATE TABLE IF NOT EXISTS saldo_bancos (
    id SERIAL PRIMARY KEY,
    banco VARCHAR(50) NOT NULL,
    saldo DECIMAL(15,2) NOT NULL,
    fecha_captura TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Crear índices básicos para mejorar las consultas
CREATE INDEX IF NOT EXISTS idx_saldo_bancos_banco ON saldo_bancos(banco);
CREATE INDEX IF NOT EXISTS idx_saldo_bancos_fecha ON saldo_bancos(fecha_captura);

-- Comentarios para documentación
COMMENT ON TABLE saldo_bancos IS 'Tabla para almacenar los saldos de diferentes bancos';
COMMENT ON COLUMN saldo_bancos.banco IS 'Nombre del banco (ej: BCI, Santander)';
COMMENT ON COLUMN saldo_bancos.saldo IS 'Saldo de la cuenta en el banco';
COMMENT ON COLUMN saldo_bancos.fecha_captura IS 'Fecha y hora cuando se capturó el saldo';
COMMENT ON COLUMN saldo_bancos.created_at IS 'Fecha y hora de creación del registro';
"""
                
                print(sql_script)
                logger.info("=" * 60)
                logger.info("🌐 Dashboard URL: https://tmimwpzxmtezopieqzcl.supabase.co")
                logger.info("📍 Ve a: SQL Editor > New Query > Pega el SQL > Run")
                return False
            else:
                logger.error(f"❌ Error inesperado al verificar la tabla: {str(table_error)}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Error de conexión: {str(e)}")
        return False

def test_table_operations():
    """Prueba las operaciones básicas de la tabla"""
    try:
        supabase = create_client(
            SUPABASE_CONFIG["url"],
            SUPABASE_CONFIG["key"]
        )
        
        logger.info("🧪 Probando operaciones de la tabla...")
        
        # Probar inserción de datos de prueba
        test_data = {
            "banco": "test_banco",
            "saldo": 1000.50
        }
        
        result = supabase.table('saldo_bancos').insert(test_data).execute()
        logger.info("✅ Inserción de prueba exitosa")
        
        # Probar consulta
        query_result = supabase.table('saldo_bancos').select('*').eq('banco', 'test_banco').execute()
        logger.info(f"✅ Consulta exitosa. Registros encontrados: {len(query_result.data)}")
        
        # Limpiar datos de prueba
        delete_result = supabase.table('saldo_bancos').delete().eq('banco', 'test_banco').execute()
        logger.info("✅ Limpieza de datos de prueba exitosa")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en pruebas: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Verificando tabla saldo_bancos...")
    
    if verify_and_create_table():
        logger.info("🧪 Ejecutando pruebas de la tabla...")
        if test_table_operations():
            logger.info("🎉 ¡Todo funciona correctamente!")
        else:
            logger.error("💥 Error en las pruebas de la tabla")
    else:
        logger.info("⚠️  La tabla necesita ser creada manualmente")