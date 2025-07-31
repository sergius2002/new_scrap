#!/bin/bash
# Script para ejecutar el scraper de Santander

echo "🏪 Iniciando Scraper Santander..."
echo "Directorio: $(pwd)"
echo "Fecha: $(date)"
echo "================================"

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    echo "Activando entorno virtual..."
    source venv/bin/activate
fi

# Ejecutar el scraper
python3 Scrap_santander.py

echo "================================"
echo "Scraper Santander finalizado: $(date)"