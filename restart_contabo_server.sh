#!/bin/bash

# Script para reiniciar el servidor Contabo usando la API
# Credenciales de la API
CLIENT_ID="INT-14090128"
CLIENT_SECRET="kjvBdqOZRoZ37Gsj5LVl37Lx6MBJrmwM"
API_PASSWORD="Kj6mm866.-"

echo "🔑 Obteniendo token de acceso..."

# Obtener token de acceso usando username/password
TOKEN_RESPONSE=$(curl -s -X POST "https://auth.contabo.com/auth/realms/contabo/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&client_id=${CLIENT_ID}&client_secret=${CLIENT_SECRET}&username=sergio.plaza.altamirano@gmail.com&password=${API_PASSWORD}")

# Extraer el token de acceso
ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$ACCESS_TOKEN" ]; then
    echo "❌ Error: No se pudo obtener el token de acceso"
    echo "Respuesta: $TOKEN_RESPONSE"
    exit 1
fi

echo "✅ Token obtenido exitosamente"

# Obtener lista de instancias
echo "📋 Obteniendo lista de instancias..."
INSTANCES_RESPONSE=$(curl -s -X GET "https://api.contabo.com/v1/compute/instances" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "x-request-id: $(uuidgen)")

echo "📊 Instancias disponibles:"
echo $INSTANCES_RESPONSE | jq -r '.data[] | "ID: \(.instanceId) - Nombre: \(.displayName) - IP: \(.ipConfig.v4.ip) - Estado: \(.status)"' 2>/dev/null || echo $INSTANCES_RESPONSE

# Buscar la instancia por IP (85.190.254.173)
INSTANCE_ID=$(echo $INSTANCES_RESPONSE | jq -r '.data[] | select(.ipConfig.v4.ip == "85.190.254.173") | .instanceId' 2>/dev/null)

if [ -z "$INSTANCE_ID" ]; then
    echo "❌ Error: No se encontró la instancia con IP 85.190.254.173"
    echo "Por favor, selecciona manualmente el Instance ID de la lista anterior"
    exit 1
fi

echo "🎯 Instancia encontrada: $INSTANCE_ID"

# Confirmar reinicio
echo "⚠️  ¿Estás seguro de que quieres reiniciar el servidor?"
echo "   IP: 85.190.254.173"
echo "   Instance ID: $INSTANCE_ID"
echo "   Tiempo estimado de inactividad: 2-3 minutos"
echo ""
read -p "Escribe 'SI' para confirmar el reinicio: " CONFIRM

if [ "$CONFIRM" != "SI" ]; then
    echo "❌ Reinicio cancelado"
    exit 0
fi

# Reiniciar la instancia
echo "🔄 Iniciando reinicio del servidor..."
RESTART_RESPONSE=$(curl -s -X POST "https://api.contabo.com/v1/compute/instances/${INSTANCE_ID}/actions/restart" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "x-request-id: $(uuidgen)" \
  -H "Content-Type: application/json" \
  -d '{}')

echo "📤 Respuesta del reinicio:"
echo $RESTART_RESPONSE | jq . 2>/dev/null || echo $RESTART_RESPONSE

# Verificar si el reinicio fue exitoso
if echo $RESTART_RESPONSE | grep -q '"action":"restart"' 2>/dev/null; then
    echo "✅ Reinicio iniciado exitosamente"
    echo "⏱️  El servidor estará disponible en 2-3 minutos"
    echo "🔍 Puedes verificar el estado con: ssh contabo 'uptime'"
else
    echo "❌ Error en el reinicio"
    echo "Respuesta: $RESTART_RESPONSE"
fi