#!/bin/bash

# Script para escanear carpetas y encontrar el proyecto en Contabo
# Uso: ./scan_contabo_folders.sh

SERVER="root@85.190.254.173"

echo "🔍 Escaneando carpetas en servidor Contabo..."
echo "🌐 Servidor: $SERVER"
echo "=" | tr '=' '=' | head -c 50; echo

ssh $SERVER << 'EOF'
    echo "📁 DIRECTORIO HOME:"
    pwd
    echo ""
    
    echo "📂 CONTENIDO DEL DIRECTORIO ACTUAL:"
    ls -la
    echo ""
    
    echo "🔍 BUSCANDO PROYECTOS DE SCRAPING..."
    echo "Buscando archivos Python relacionados con scraping:"
    find / -name "*scrap*" -type f 2>/dev/null | head -20
    echo ""
    
    echo "🔍 BUSCANDO ARCHIVOS SUPERVISOR:"
    find / -name "supervisor.py" -type f 2>/dev/null
    echo ""
    
    echo "🔍 BUSCANDO ARCHIVOS SANTANDER:"
    find / -name "*santander*" -type f 2>/dev/null | head -10
    echo ""
    
    echo "🔍 BUSCANDO ARCHIVOS BCI:"
    find / -name "*bci*" -type f 2>/dev/null | head -10
    echo ""
    
    echo "🔍 BUSCANDO REPOSITORIOS GIT:"
    find / -name ".git" -type d 2>/dev/null | head -10
    echo ""
    
    echo "📋 DIRECTORIOS EN /root:"
    if [ -d "/root" ]; then
        ls -la /root/
    fi
    echo ""
    
    echo "📋 DIRECTORIOS EN /home:"
    if [ -d "/home" ]; then
        ls -la /home/
    fi
    echo ""
    
    echo "🔍 BUSCANDO ARCHIVOS requirements.txt:"
    find / -name "requirements.txt" -type f 2>/dev/null | head -10
    echo ""
    
    echo "🔍 PROCESOS PYTHON ACTIVOS:"
    ps aux | grep python | grep -v grep
    echo ""
    
    echo "🔍 SERVICIOS SYSTEMD RELACIONADOS:"
    systemctl list-units --type=service | grep -i scrap || echo "No se encontraron servicios de scraping"
    
EOF

echo ""
echo "✅ Escaneo completado!"