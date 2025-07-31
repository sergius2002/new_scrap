#!/bin/bash
# Script para ejecutar el scraper de Banco Estado

echo "🏛️ Iniciando Scraper Banco Estado..."
echo "Directorio: $(pwd)"
echo "Fecha: $(date)"
echo "================================"

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    echo "Activando entorno virtual..."
    source venv/bin/activate
fi

# Ejecutar el scraper
python3 Scrap_estado.py

echo "================================"
echo "Scraper Banco Estado finalizado: $(date)"