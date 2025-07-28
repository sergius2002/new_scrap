# 🚀 Scrapers Activos en el Supervisor

## ✅ Scrapers configurados para ejecutarse:

### 1. **Scrap_bci.py** 
- **Banco:** BCI (Banco de Crédito e Inversiones)
- **Estado:** ✅ ACTIVO
- **Tamaño:** 37,247 bytes

### 2. **Scrap_santander.py**
- **Banco:** Santander
- **Estado:** ✅ ACTIVO  
- **Tamaño:** 18,736 bytes

### 3. **Scrap_estado.py**
- **Banco:** Banco del Estado
- **Estado:** ✅ ACTIVO
- **Tamaño:** 26,620 bytes

### 4. **Facturador_lioren.py**
- **Servicio:** Facturación Lioren
- **Estado:** ✅ ACTIVO
- **Tamaño:** 26,163 bytes

## 📊 Funcionalidades del Supervisor:

- 🔄 **Monitoreo automático** cada minuto
- 🔄 **Reinicio automático** si algún scraper se cae
- 📧 **Notificaciones por email** cuando hay problemas
- 🧹 **Limpieza automática** de procesos Chrome huérfanos
- 📈 **Reportes diarios** a las 8:00 AM
- 📧 **Email de notificaciones:** sergio.plaza.altamirano@gmail.com

## 🔗 Conexión VNC - Instrucciones Paso a Paso

### Paso 1: Verificar que el túnel SSH esté activo
El túnel SSH debe estar ejecutándose en segundo plano. Si no está activo, ejecuta:
```bash
ssh -L 63109:localhost:63109 root@85.190.254.173
```
Contraseña SSH: `kj6mm866`

### Paso 2: Abrir RealVNC Viewer
1. Abre la aplicación **RealVNC Viewer** en tu Mac
2. En la barra de dirección, ingresa: `localhost:63109`
3. Haz clic en **"Conectar"**

### Paso 3: Autenticación VNC
1. Aparecerá una ventana de autenticación
2. Ingresa la contraseña: `rxyKY8xZ`
3. Haz clic en **"Aceptar"**

### Paso 4: Entorno de escritorio
- Verás el entorno de escritorio **XFCE** del servidor
- Tendrás acceso completo al escritorio Linux
- **Click derecho funcionando** ✅
- **Copiar y pegar funcionando** ✅
- **Terminal gráfica disponible** ✅

### Paso 5: Ejecutar los scrapers
1. **Abre una terminal** (click derecho en el escritorio → Terminal)
2. **Ejecuta los comandos:**
```bash
cd /home/scraper/new_scrap
source venv/bin/activate
python3 supervisor.py
```

## 🎯 Comandos para ejecutar:

```bash
cd /home/scraper/new_scrap
source venv/bin/activate
python3 supervisor.py
```

## 📝 Notas importantes:
- **Mantén el túnel SSH activo** mientras uses VNC
- **Todos los scrapers se ejecutarán automáticamente**
- **El supervisor los mantendrá visibles y funcionando**
- **Si algún scraper se cae, se reiniciará automáticamente**
- **Recibirás notificaciones por email si hay problemas**
- **Para desconectar VNC:** Cierra la ventana de RealVNC Viewer
- **Para detener el túnel SSH:** Ctrl+C en la terminal donde está ejecutándose

## 🔧 Solución de problemas VNC:

### Si la conexión es rechazada:
1. Verifica que el túnel SSH esté activo: `lsof -i :63109`
2. Asegúrate de usar `localhost:63109` (no la IP externa)
3. Verifica que VNC esté ejecutándose en el servidor

### Para reiniciar VNC en el servidor:
```bash
echo "kj6mm866" | ssh root@85.190.254.173 "vncserver -kill :1 && vncserver :1 -geometry 1920x1080 -depth 24 -localhost no -rfbport 63109 -xstartup /usr/bin/startxfce4"
``` 