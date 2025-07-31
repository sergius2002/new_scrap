#!/bin/bash
# Script para ejecutar el facturador Lioren

echo "📄 Iniciando Facturador Lioren..."
echo "Directorio: $(pwd)"
echo "Fecha: $(date)"
echo "================================"

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    echo "Activando entorno virtual..."
    source venv/bin/activate
fi

# Ejecutar el facturador
python3 Facturador_lioren.py

echo "================================"
echo "Facturador Lioren finalizado: $(date)"