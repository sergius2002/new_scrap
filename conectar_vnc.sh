#!/bin/bash

# Script para conectar al túnel VNC del servidor Contabo
# Uso: ./conectar_vnc.sh

echo "🔗 Conectando al túnel VNC..."
echo "📡 Servidor: 85.190.254.173"
echo "🔌 Puerto: 63109"
echo ""

# Verificar si ya hay un túnel activo
if lsof -i :63109 > /dev/null 2>&1; then
    echo "⚠️  Ya hay un túnel SSH activo en el puerto 63109"
    echo "   PID: $(lsof -ti :63109)"
    echo ""
    read -p "¿Deseas terminar el túnel existente y crear uno nuevo? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🔄 Terminando túnel existente..."
        lsof -ti :63109 | xargs kill
        sleep 2
    else
        echo "✅ Usando túnel existente"
        echo ""
        echo "🎯 Ahora puedes conectar con RealVNC Viewer usando:"
        echo "   Dirección: localhost:63109"
        echo "   Contraseña: rxyKY8xZ"
        exit 0
    fi
fi

echo "🚀 Estableciendo nuevo túnel SSH..."
ssh -L 63109:localhost:63109 contabo -N &

# Esperar un momento para que se establezca la conexión
sleep 3

# Verificar que el túnel esté funcionando
if lsof -i :63109 > /dev/null 2>&1; then
    echo "✅ Túnel SSH establecido exitosamente!"
    echo "   PID: $(lsof -ti :63109)"
    echo ""
    echo "🎯 Ahora puedes conectar con RealVNC Viewer usando:"
    echo "   Dirección: localhost:63109"
    echo "   Contraseña: rxyKY8xZ"
    echo ""
    echo "💡 Para terminar el túnel, ejecuta: kill \$(lsof -ti :63109)"
else
    echo "❌ Error al establecer el túnel SSH"
    exit 1
fi 