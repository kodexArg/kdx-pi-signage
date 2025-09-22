# Sistema de Cartelería Digital KDX - Raspberry Pi 3 A+

Sistema de cartelería digital autónomo diseñado específicamente para **Raspberry Pi 3 A+** que reproduce videos en bucle continuo de forma completamente automática.

## 🎯 Características Principales

- **Reproducción automática**: Escaneo y reproducción continua de videos desde directorio `/videos/`
- **Monitoreo en tiempo real**: Detección automática de cambios en el directorio de videos
- **Gestión robusta de errores**: Sistema de reintentos y recuperación automática
- **Optimizado para Pi 3 A+**: Configuración específica para hardware con 512MB RAM
- **Servicio systemd**: Auto-inicio y gestión automática del sistema
- **Logging avanzado**: Sistema de logs con rotación automática usando loguru

## 🏗️ Arquitectura del Sistema

El sistema implementa varios patrones de diseño para garantizar robustez y mantenibilidad:

- **Patrón Facade**: `SignageSystem` coordina todos los componentes
- **Patrón Adapter**: `VideoPlayer` adapta VLC Media Player
- **Patrón Strategy**: `PlaylistManager` con diferentes estrategias de reproducción
- **Patrón Observer**: `VideoScanner` monitorea cambios en el directorio
- **Patrón Singleton**: `Logger` para logging centralizado

## 📋 Requisitos del Sistema

### Hardware
- **Raspberry Pi 3 A+** (512MB RAM)
- Tarjeta microSD 32GB+ (Clase 10 recomendada)
- Pantalla HDMI 1920x1080

### Software
- **Raspberry Pi OS Lite** (headless)
- **Python 3.9+**
- **VLC Media Player**
- **uv** (gestor de paquetes)

## 🚀 Instalación

### 1. Preparar el Sistema

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias del sistema
sudo apt install -y vlc python3-pip git

# Instalar uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

### 2. Clonar e Instalar el Proyecto

```bash
# Clonar repositorio
git clone https://github.com/kodex/kdx-pi-signage.git
cd kdx-pi-signage

# Instalar dependencias con uv
uv sync

# Crear directorios necesarios
mkdir -p videos logs
```

### 3. Configurar Auto-login (Opcional)

```bash
# Habilitar auto-login para usuario pi
sudo raspi-config nonint do_boot_behaviour B2
```

### 4. Instalar Servicio Systemd

```bash
# Copiar archivo de servicio
sudo cp kdx-pi-signage.service ~/.config/systemd/user/

# Habilitar servicio
systemctl --user daemon-reload
systemctl --user enable kdx-pi-signage.service
systemctl --user start kdx-pi-signage.service
```

## 📁 Estructura del Proyecto

```
kdx-pi-signage/
├── main.py                 # Aplicación principal
├── logger.py              # Sistema de logging (Singleton)
├── config.py              # Modelos de configuración (Pydantic)
├── video_player.py        # Reproductor VLC (Adapter)
├── playlist_manager.py    # Gestor de playlist (Strategy)
├── video_scanner.py       # Monitor de directorio (Observer)
├── pyproject.toml         # Configuración del proyecto
├── kdx-pi-signage.service # Archivo de servicio systemd
├── videos/                # Directorio de videos
├── logs/                  # Logs del sistema
└── README.md             # Este archivo
```

## 🎬 Uso del Sistema

### Agregar Videos

1. Copiar archivos de video al directorio `videos/`:
   ```bash
   cp mi_video.mp4 /home/pi/kdx-pi-signage/videos/
   ```

2. El sistema detectará automáticamente los nuevos videos y actualizará la playlist.

### Formatos Soportados

- **MP4** (recomendado)
- **AVI**
- **MKV**
- **MOV**
- **WMV**

### Especificaciones Recomendadas

- **Resolución**: 1920x1080 (Full HD)
- **Códec**: H.264 con aceleración de hardware
- **Bitrate**: 6-8 Mbps (optimizado para 512MB RAM)
- **Frame Rate**: 30 fps

## 🔧 Configuración

### Variables de Entorno

El sistema utiliza las siguientes variables de entorno (configuradas automáticamente):

```bash
DISPLAY=:0
VIDEO_DIR=/home/pi/kdx-pi-signage/videos
LOG_DIR=/home/pi/kdx-pi-signage/logs
LOG_LEVEL=INFO
```

### Configuración de VLC

El sistema está optimizado para Raspberry Pi 3 A+ con las siguientes opciones:

- Interfaz: `dummy` (modo headless)
- Salida de video: `mmal_vout` (aceleración de hardware)
- Códec: `mmal` (decodificación por hardware)
- Pantalla completa: Habilitada
- Audio: Deshabilitado (para ahorrar RAM)

## 📊 Monitoreo y Logs

### Ubicación de Logs

- **Log principal**: `/home/pi/kdx-pi-signage/logs/signage.log`
- **Log de errores**: `/home/pi/kdx-pi-signage/logs/errors.log`

### Ver Logs en Tiempo Real

```bash
# Log del servicio systemd
journalctl --user -u kdx-pi-signage.service -f

# Log de la aplicación
tail -f /home/pi/kdx-pi-signage/logs/signage.log
```

### Estado del Servicio

```bash
# Ver estado
systemctl --user status kdx-pi-signage.service

# Reiniciar servicio
systemctl --user restart kdx-pi-signage.service

# Detener servicio
systemctl --user stop kdx-pi-signage.service
```

## 🛠️ Desarrollo

### Ejecutar en Modo Desarrollo

```bash
# Activar entorno virtual
source .venv/bin/activate

# Ejecutar aplicación
python main.py
```

### Estructura de Clases Principales

#### `SignageSystem` (Facade Pattern)
Coordina todos los componentes del sistema y proporciona una interfaz unificada.

#### `VideoPlayer` (Adapter Pattern)
Adapta VLC Media Player para el sistema de cartelería con configuración optimizada.

#### `PlaylistManager` (Strategy Pattern)
Gestiona listas de reproducción con diferentes estrategias (secuencial, aleatoria).

#### `VideoScanner` (Observer Pattern)
Monitorea cambios en el directorio de videos usando watchdog.

#### `Logger` (Singleton Pattern)
Sistema de logging centralizado con rotación automática.

## 🔍 Solución de Problemas

### El sistema no inicia

1. Verificar que VLC esté instalado:
   ```bash
   vlc --version
   ```

2. Verificar permisos del directorio:
   ```bash
   ls -la /home/pi/kdx-pi-signage/
   ```

3. Revisar logs del servicio:
   ```bash
   journalctl --user -u kdx-pi-signage.service --no-pager
   ```

### Videos no se reproducen

1. Verificar formato de video soportado
2. Comprobar que el archivo no esté corrupto:
   ```bash
   vlc --intf dummy video.mp4
   ```

3. Verificar espacio en disco:
   ```bash
   df -h
   ```

### Problemas de rendimiento

1. Verificar temperatura del Pi:
   ```bash
   vcgencmd measure_temp
   ```

2. Verificar uso de memoria:
   ```bash
   free -h
   ```

3. Optimizar videos para Pi 3 A+:
   ```bash
   ffmpeg -i input.mp4 -c:v h264_omx -b:v 6M -vf scale=1920:1080 output.mp4
   ```

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## 📞 Soporte

Para soporte técnico o reportar problemas:

- **Issues**: [GitHub Issues](https://github.com/kodex/kdx-pi-signage/issues)
- **Documentación**: Ver archivos en `.trae/documents/`

---

**Desarrollado con ❤️ para Raspberry Pi 3 A+**