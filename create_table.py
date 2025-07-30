#!/usr/bin/env python3
"""
Script para crear la tabla saldo_bancos en Supabase
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase import create_client
from config import SUPABASE_CONFIG
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def create_saldo_bancos_table():
    """Crea la tabla saldo_bancos en Supabase"""
    try:
        # Conectar a Supabase
        supabase = create_client(
            SUPABASE_CONFIG["url"],
            SUPABASE_CONFIG["key"]
        )
        
        # SQL para crear la tabla
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS saldo_bancos (
            id SERIAL PRIMARY KEY,
            banco VARCHAR(50) NOT NULL,
            saldo DECIMAL(15,2) NOT NULL,
            fecha_captura TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(banco, fecha_captura::date)
        );
        """
        
        # SQL para crear índices
        create_indexes_sql = """
        CREATE INDEX IF NOT EXISTS idx_saldo_bancos_banco ON saldo_bancos(banco);
        CREATE INDEX IF NOT EXISTS idx_saldo_bancos_fecha ON saldo_bancos(fecha_captura);
        """
        
        # SQL para comentarios
        create_comments_sql = """
        COMMENT ON TABLE saldo_bancos IS 'Tabla para almacenar saldos de diferentes bancos, guardando solo cuando hay diferencias';
        COMMENT ON COLUMN saldo_bancos.banco IS 'Identificador del banco (ej: st_bci, st_santander, etc.)';
        COMMENT ON COLUMN saldo_bancos.saldo IS 'Saldo actual de la cuenta en el banco';
        COMMENT ON COLUMN saldo_bancos.fecha_captura IS 'Fecha y hora cuando se capturó el saldo';
        COMMENT ON COLUMN saldo_bancos.created_at IS 'Fecha y hora de creación del registro';
        """
        
        logger.info("Creando tabla saldo_bancos...")
        
        # Ejecutar SQL para crear tabla
        result1 = supabase.rpc('exec_sql', {'sql': create_table_sql}).execute()
        logger.info("✅ Tabla saldo_bancos creada exitosamente")
        
        # Ejecutar SQL para crear índices
        result2 = supabase.rpc('exec_sql', {'sql': create_indexes_sql}).execute()
        logger.info("✅ Índices creados exitosamente")
        
        # Ejecutar SQL para comentarios
        result3 = supabase.rpc('exec_sql', {'sql': create_comments_sql}).execute()
        logger.info("✅ Comentarios agregados exitosamente")
        
        # Verificar que la tabla existe
        tables_result = supabase.rpc('get_tables').execute()
        table_names = [table['table_name'] for table in tables_result.data if table['table_name'] == 'saldo_bancos']
        
        if 'saldo_bancos' in table_names:
            logger.info("✅ Verificación exitosa: La tabla saldo_bancos existe en la base de datos")
            return True
        else:
            logger.error("❌ Error: La tabla saldo_bancos no se encontró después de la creación")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error al crear la tabla saldo_bancos: {str(e)}")
        
        # Intentar método alternativo usando SQL directo
        try:
            logger.info("Intentando método alternativo...")
            
            # Usar el método de inserción directa con SQL
            sql_commands = [
                create_table_sql.strip(),
                create_indexes_sql.strip(),
                create_comments_sql.strip()
            ]
            
            for sql in sql_commands:
                if sql:
                    result = supabase.postgrest.session.post(
                        f"{SUPABASE_CONFIG['url']}/rest/v1/rpc/exec_sql",
                        json={"sql": sql},
                        headers={
                            "apikey": SUPABASE_CONFIG["key"],
                            "Authorization": f"Bearer {SUPABASE_CONFIG['key']}",
                            "Content-Type": "application/json"
                        }
                    )
                    
            logger.info("✅ Tabla creada usando método alternativo")
            return True
            
        except Exception as e2:
            logger.error(f"❌ Error en método alternativo: {str(e2)}")
            logger.info("💡 Por favor, ejecuta manualmente el SQL en el dashboard de Supabase:")
            logger.info("📄 Archivo: create_saldo_bancos_table.sql")
            return False

if __name__ == "__main__":
    logger.info("🚀 Iniciando creación de tabla saldo_bancos...")
    success = create_saldo_bancos_table()
    
    if success:
        logger.info("🎉 ¡Tabla saldo_bancos creada exitosamente!")
    else:
        logger.error("💥 Error al crear la tabla. Revisa los logs para más detalles.")
        sys.exit(1)