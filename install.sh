#!/bin/bash

# Script de instalación para el Sistema de Facturación Automática
echo "🚀 Instalando Sistema de Facturación Automática - San Cristóbal"
echo "================================================================"

# Verificar si Python 3.9+ está instalado
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    echo "✅ Python $python_version detectado (cumple requisitos)"
else
    echo "❌ Error: Se requiere Python 3.9 o superior. Versión actual: $python_version"
    exit 1
fi

# Crear entorno virtual
echo "📦 Creando entorno virtual..."
if [ -d ".venv" ]; then
    echo "⚠️  El entorno virtual ya existe. Eliminando..."
    rm -rf .venv
fi

python3 -m venv .venv
if [ $? -ne 0 ]; then
    echo "❌ Error al crear el entorno virtual"
    exit 1
fi

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source .venv/bin/activate

# Actualizar pip
echo "⬆️  Actualizando pip..."
pip install --upgrade pip

# Instalar dependencias principales
echo "📚 Instalando dependencias principales..."
pip install supabase python-dotenv requests pandas openpyxl playwright

if [ $? -ne 0 ]; then
    echo "❌ Error al instalar dependencias principales"
    exit 1
fi

# Instalar navegadores de Playwright
echo "🌐 Instalando navegadores de Playwright..."
playwright install

if [ $? -ne 0 ]; then
    echo "❌ Error al instalar navegadores de Playwright"
    exit 1
fi

# Crear archivo .env si no existe
if [ ! -f ".env" ]; then
    echo "📝 Creando archivo .env de ejemplo..."
    if [ -f "env.example" ]; then
        cp env.example .env
        echo "⚠️  IMPORTANTE: Edita el archivo .env con tus credenciales reales"
    else
        echo "⚠️  No se encontró env.example. Crea manualmente el archivo .env"
    fi
else
    echo "✅ Archivo .env ya existe"
fi

# Crear directorios necesarios
echo "📁 Creando directorios necesarios..."
mkdir -p output logs certificado

# Verificar instalación
echo "🧪 Verificando instalación..."
python3 -c "
import sys
try:
    import supabase
    import pandas
    import openpyxl
    import playwright
    print('✅ Todas las dependencias instaladas correctamente')
except ImportError as e:
    print(f'❌ Error de importación: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 ¡Instalación completada exitosamente!"
    echo ""
    echo "📋 Próximos pasos:"
    echo "1. Edita el archivo .env con tus credenciales reales"
    echo "2. Activa el entorno virtual: source .venv/bin/activate"
    echo "3. Ejecuta el sistema: python src/main.py"
    echo ""
    echo "📖 Para más información, consulta el README.md"
else
    echo "❌ Error en la verificación de instalación"
    exit 1
fi 