#!/bin/bash

echo "🔄 Reiniciando procesos en servidor Contabo..."
echo "📡 Servidor: 85.190.254.173"
echo ""

# Conectar al servidor y ejecutar comandos de reinicio
ssh contabo << 'EOF'
echo "🏠 Navegando al directorio del proyecto..."
cd /home/scraper/new_scrap

echo "🔍 Verificando procesos actuales..."
ps aux | grep -E "(supervisor|Scrap_|Facturador_)" | grep -v grep

echo ""
echo "🛑 Deteniendo procesos obsoletos..."
pkill -f supervisor.py 2>/dev/null || echo "   ℹ️  No hay supervisor corriendo"
pkill -f Scrap_bci.py 2>/dev/null || echo "   ℹ️  No hay Scrap_bci corriendo"
pkill -f Scrap_santander.py 2>/dev/null || echo "   ℹ️  No hay Scrap_santander corriendo"
pkill -f Scrap_estado.py 2>/dev/null || echo "   ℹ️  No hay Scrap_estado corriendo"
pkill -f Facturador_lioren.py 2>/dev/null || echo "   ℹ️  No hay Facturador corriendo"

echo ""
echo "⏳ Esperando 3 segundos..."
sleep 3

echo ""
echo "🚀 Iniciando supervisor con código actualizado..."
nohup python3 supervisor.py > supervisor.log 2>&1 &

echo ""
echo "⏳ Esperando 5 segundos para que inicie..."
sleep 5

echo ""
echo "✅ Verificando nuevos procesos:"
ps aux | grep -E "(supervisor|Scrap_|Facturador_)" | grep -v grep

echo ""
echo "📋 Últimas líneas del log del supervisor:"
tail -10 supervisor.log 2>/dev/null || echo "   ⚠️  Log no disponible aún"

echo ""
echo "🎯 Reinicio completado!"
EOF

echo ""
echo "✨ Proceso de reinicio terminado!"