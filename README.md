# Sistema de Supervisión de Scripts

## Descripción del Proyecto

Este proyecto implementa un sistema de supervisión automatizada para múltiples scripts de scraping bancario y facturación. El supervisor (`supervisor.py`) monitorea continuamente la ejecución de los siguientes scripts:

- **Scrap_bci.py**: Scraper para el banco BCI
- **Scrap_estado.py**: Scraper para Banco Estado
- **Facturador_lioren.py**: Sistema de facturación Lioren

El supervisor se encarga de:
- Iniciar automáticamente los scripts configurados
- Reiniciar scripts que se detengan inesperadamente
- Limpiar procesos de Chrome huérfanos cada 5 minutos
- Registrar todas las actividades en un archivo de log

## Instrucciones de Instalación y Ejecución

### 1. Activar el Entorno Virtual

El proyecto ya incluye un entorno virtual configurado. Para activarlo:

```bash
# En macOS/Linux
source .venv/bin/activate

# En Windows
.venv\Scripts\activate
```

### 2. Ejecutar el Supervisor

Una vez activado el entorno virtual, ejecutar:

```bash
python3 supervisor.py
```

El supervisor se ejecutará en segundo plano y comenzará a monitorear los scripts configurados.

### 3. Verificar el Funcionamiento

Para verificar que el supervisor está funcionando correctamente:

```bash
# Verificar procesos en ejecución
ps aux | grep supervisor.py

# Verificar el archivo de log
tail -f supervisor_scripts.log
```

## Requisitos del Sistema

### Software Requerido
- Python 3.9 o superior
- pip3 (gestor de paquetes de Python)

### Dependencias Principales
- `psutil`: Monitoreo de procesos del sistema
- `playwright`: Automatización de navegadores web
- `pandas`: Manipulación de datos
- `requests`: Peticiones HTTP
- `beautifulsoup4`: Parsing de HTML
- `python-telegram-bot`: Integración con Telegram
- `supabase`: Base de datos en la nube

### Configuración del Navegador
- El sistema utiliza Playwright para automatización web
- Se requiere Chrome/Chromium instalado en el sistema

## Configuración

### Scripts Habilitados
Los scripts que se ejecutan están configurados en la variable `ENABLED_SCRIPTS` dentro de `supervisor.py`:

```python
ENABLED_SCRIPTS = [
    "Scrap_bci.py",
    "Scrap_estado.py", 
    "Facturador_lioren.py"
]
```

### Logs
El supervisor genera logs detallados en el archivo `supervisor_scripts.log` que incluyen:
- Inicio y parada de scripts
- Errores y reinicios automáticos
- Limpieza de recursos del sistema

## Notas Importantes

- El supervisor verifica el estado de los scripts cada minuto
- La limpieza de procesos Chrome huérfanos se realiza cada 5 minutos
- Todos los scripts se ejecutan en el directorio del proyecto
- El sistema está diseñado para ejecutarse de forma continua

## Solución de Problemas

Si encuentras problemas con la ejecución:

1. **Verificar entorno virtual**: Asegúrate de que el entorno virtual esté activado
2. **Verificar dependencias**: Ejecuta `pip3 list` para confirmar que todas las dependencias estén instaladas
3. **Revisar logs**: Consulta `supervisor_scripts.log` para identificar errores específicos
4. **Verificar permisos**: Asegúrate de tener permisos de ejecución en los archivos Python

### Problemas Comunes Resueltos

#### Error de Supabase (TypeError: __init__() got an unexpected keyword argument 'proxy')
Si encuentras este error al ejecutar `bci.py` o scripts que usan Supabase:

```bash
# Actualizar las dependencias de Supabase
source .venv/bin/activate
pip3 install --upgrade supabase gotrue httpx
```

Este problema se debe a incompatibilidades de versiones entre las librerías de Supabase y se resuelve actualizando a las versiones más recientes.

#### Error de certificado Gmail en Facturador Lioren
Si el facturador falla con el error `No such file or directory: 'certificado/lioren-446620-e63e8a6e22d4.json'`:

**Solución**: El problema ya está corregido en el código. El facturador ahora usa la variable de entorno `CREDENTIALS_PATH` del archivo `.env` en lugar de una ruta hardcodeada.

**Verificar**: Asegúrate de que el archivo `.env` contenga:
```env
CREDENTIALS_PATH=certificado/lioren-446620-e63e8a6e22d4.json
TOKEN_PATH=certificado/token.json
```

#### Scripts que no se ejecutan
- **bci.py**: No usa navegador, lee archivo Excel de `Bancos/excel_detallado.xlsx`
- **Scrap_estado.py**: Usa Playwright para automatización web
- **Facturador_lioren.py**: Procesa facturas desde la base de datos

### Estado Actual del Sistema

✅ **supervisor.py**: Funcionando correctamente
✅ **bci.py**: Funcionando correctamente (problema de dependencias resuelto)
✅ **Scrap_estado.py**: Funcionando correctamente
✅ **Facturador_lioren.py**: Funcionando correctamente (problema de certificado resuelto)

El supervisor está funcionando correctamente en el entorno virtual y todas las dependencias necesarias están instaladas.

---

**Última actualización:** Diciembre 2024
**Versión del sistema:** 1.0 