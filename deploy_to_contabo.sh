#!/bin/bash

# Script para hacer git pull en el servidor Contabo
# Uso: ./deploy_to_contabo.sh

SERVER="root@85.190.254.173"
PROJECT_PATH="/home/scraper/new_scrap"  # Ruta encontrada en el escaneo

echo "🚀 Conectando al servidor Contabo..."
echo "📁 Navegando al directorio del proyecto: $PROJECT_PATH"
echo "🔄 Haciendo git pull..."

ssh $SERVER << EOF
    cd $PROJECT_PATH
    echo "📍 Directorio actual: \$(pwd)"
    echo "🔍 Estado del repositorio:"
    git status
    echo ""
    echo "⬇️  Descargando cambios..."
    git pull origin main
    echo ""
    echo "✅ Últimos commits:"
    git log --oneline -3
    echo ""
    echo "🎯 Git pull completado!"
    echo ""
    echo "🔄 Estado de procesos activos:"
    ps aux | grep python | grep -E "(supervisor|scrap)" | grep -v grep
EOF

echo "✨ Proceso terminado!"