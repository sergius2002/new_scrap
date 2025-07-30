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