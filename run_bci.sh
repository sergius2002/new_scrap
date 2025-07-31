#!/bin/bash
# Script para ejecutar el scraper de BCI

echo "🏦 Iniciando Scraper BCI..."
echo "Directorio: $(pwd)"
echo "Fecha: $(date)"
echo "================================"

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    echo "Activando entorno virtual..."
    source venv/bin/activate
fi

# Ejecutar el scraper
python3 Scrap_bci.py

echo "================================"
echo "Scraper BCI finalizado: $(date)"