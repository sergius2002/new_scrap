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

## Ejemplo de conexión SSH exitosa
Cuando la conexión SSH es exitosa, verás algo como:
```
root@85.190.254.173's password: 
Welcome to Ubuntu 24.04.2 LTS (GNU/Linux 6.8.0-64-generic x86_64)
 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro
 System information as of Wed Jul 30 15:51:31 CEST 2025
  System load:  0.56              Processes:             250
  Usage of /:   9.4% of 95.82GB   Users logged in:       0
  Memory usage: 13%               IPv4 address for eth0: 85.190.254.173
  Swap usage:   0%                IPv6 address for eth0: 2a02:c207:2271:8061::1
 * Strictly confined Kubernetes makes edge and IoT secure. Learn how MicroK8s
   just raised the bar for easy, resilient and secure K8s cluster deployment.
   https://ubuntu.com/engage/secure-kubernetes-at-the-edge
Expanded Security Maintenance for Applications is not enabled.
24 updates can be applied immediately.
17 of these updates are standard security updates.
To see these additional updates run: apt list --upgradable
13 additional security updates can be applied with ESM Apps.
Learn more about enabling ESM Apps service at https://ubuntu.com/esm
  _____
 / ___/___  _  _ _____ _   ___  ___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/
Welcome!
This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.
Last login: Mon Jul 28 19:49:08 2025 from 190.90.86.81
root@vmi2718061:~# 
```

**Una vez que veas este mensaje, el túnel SSH está establecido y puedes proceder con VNC.**

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