# Instrucciones para conectar a VNC - Servidor Contabo

## Configuración actual
- **Servidor:** 85.190.254.173 (Contabo)
- **Puerto VNC:** 63109
- **Contraseña VNC:** rxyKY8xZ
- **Usuario SSH:** root
- **Contraseña SSH:** kj6mm866

## Conexión mediante SSH Túnel

### 1. Establecer túnel SSH (ya ejecutándose)
```bash
ssh -L 63109:localhost:63109 root@85.190.254.173
```

### 2. Configuración en RealVNC Viewer
- **Dirección:** `localhost:63109`
- **Contraseña:** `rxyKY8xZ`

### 3. Pasos para conectar
1. Asegúrate de que el túnel SSH esté activo (proceso en segundo plano)
2. Abre RealVNC Viewer
3. Ingresa `localhost:63109` en la barra de dirección
4. Haz clic en "Conectar"
5. Ingresa la contraseña: `rxyKY8xZ`

## Verificación del túnel
Para verificar que el túnel esté funcionando:
```bash
lsof -i :63109
```

Deberías ver algo como:
```
COMMAND   PID        USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
ssh     53231 sergioplaza    5u  IPv6 0x646934ce8731497e      0t0  TCP localhost:63109 (LISTEN)
ssh     53231 sergioplaza    6u  IPv4 0x447cc45f5362f577      0t0  TCP localhost:63109 (LISTEN)
```

## Solución de problemas

### Si la conexión es rechazada:
1. Verifica que el túnel SSH esté activo
2. Verifica que VNC esté ejecutándose en el servidor
3. Asegúrate de usar `localhost:63109` (no la IP externa)

### Para reiniciar VNC en el servidor:
```bash
echo "kj6mm866" | ssh root@85.190.254.173 "vncserver -kill :1; vncserver :1 -geometry 1920x1080 -depth 24 -localhost no -rfbport 63109 -xstartup /usr/bin/xterm"
```

### Para verificar el estado de VNC:
```bash
echo "kj6mm866" | ssh root@85.190.254.173 "ss -tlnp | grep 63109"
```

## Notas importantes
- El túnel SSH debe mantenerse activo mientras uses VNC
- La conexión directa a `5.189.132.158:63109` no funcionará debido al firewall de Contabo
- Siempre usa `localhost:63109` para conectarte 