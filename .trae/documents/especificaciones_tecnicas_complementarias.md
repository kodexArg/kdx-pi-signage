# Especificaciones Técnicas Complementarias - Sistema de Cartelería Digital

## 1. Convenciones de Desarrollo

### 1.1 Estándares de Código

Este proyecto sigue estrictas convenciones de idioma:

**Código en Inglés:**
- Archivos: `video_player.py`, `playlist_manager.py`, `error_handler.py`
- Clases: `VideoPlayer`, `PlaylistManager`, `ErrorHandler`
- Funciones: `scan_directory()`, `play_video()`, `handle_error()`
- Variables: `video_path`, `playlist_items`, `error_count`

**Documentación en Castellano:**
- Docstrings, comentarios, documentación técnica
- Excepciones: elementos técnicos entre comillas (ej: `"VideoPlayer"`)

## 2. Configuración del Entorno de Desarrollo

### 2.1 Dependencias del Proyecto

El archivo `pyproject.toml` debe incluir las siguientes dependencias:

### 2.2 Variables de Entorno

Crear archivo `.env` en el directorio raíz con las siguientes variables (nombres en inglés):

```bash
# Configuración de video
VIDEO_DIRECTORY=/home/pi/kdx-pi-signage/videos
LOG_LEVEL=INFO
LOG_FILE=/home/pi/kdx-pi-signage/logs/signage.log

# Configuración de VLC
VLC_ARGS=--intf dummy --fullscreen --no-video-title-show
VIDEO_RESOLUTION=1920x1080

# Configuración del sistema
AUTO_RESTART=true
RESTART_DELAY=5
```

**Nota:** Las variables de entorno siempre se nombran en inglés siguiendo convenciones estándar del sistema.

### 2.3 Configuración de Auto-login

Para configurar el auto-login del usuario `pi` (comandos del sistema en inglés):

```bash
# Habilitar auto-login usando raspi-config
sudo raspi-config nonint do_boot_behaviour B2

# O configuración manual editando el archivo
sudo nano /etc/systemd/system/getty@tty1.service.d/autologin.conf
```

Contenido del archivo `autologin.conf`:
```ini
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin pi --noclear %I $TERM
```

**Explicación:** Esta configuración permite que el usuario `pi` inicie sesión automáticamente sin requerir contraseña.

## Optimización de Hardware y Rendimiento

### Aceleración de Hardware en Raspberry Pi 3 A+

El Raspberry Pi 3 A+ cuenta con las siguientes características de hardware:
- **CPU**: ARM Cortex-A53 quad-core a 1.4GHz
- **GPU**: VideoCore IV con capacidades de decodificación H.264
- **RAM**: 512MB LPDDR2
- **Aceleración de video**: Soporta decodificación H.264 por hardware

### Configuración Óptima de FFmpeg para Pi 3 A+

```python
from pydantic import BaseModel, Field
from typing import Dict, Any

class FFmpegConfig(BaseModel):
    """Configuración de FFmpeg optimizada para Raspberry Pi 3 A+.
    
    Esta clase define las opciones de FFmpeg con validación pydantic
    para garantizar configuraciones correctas.
    """
    
    video_codec: str = Field(
        default='h264_omx',
        description="Códec de video con aceleración de hardware OMX"
    )
    preset: str = Field(
        default='fast',
        description="Preset de velocidad de codificación"
    )
    crf: int = Field(
        default=25,
        ge=18,
        le=28,
        description="Calidad optimizada para 512MB RAM (18-28)"
    )
    scale: str = Field(
        default='w=1920:h=1080:force_original_aspect_ratio=decrease',
        description="Escalado de video a resolución objetivo"
    )
    pad: str = Field(
        default='1920:1080:(ow-iw)/2:(oh-ih)/2',
        description="Padding para mantener aspect ratio"
    )
    format: str = Field(
        default='mp4',
        description="Formato de contenedor de salida"
    )
    threads: int = Field(
        default=4,
        ge=1,
        le=4,
        description="Número de threads (máximo 4 cores en Pi 3 A+)"
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario para compatibilidad con código existente."""
        return self.dict()

# Instancia de configuración por defecto
FFMPEG_OPTIONS_PI3A = FFmpegConfig()
```

### Formatos de Video Recomendados para Pi 3 A+

#### Especificaciones Técnicas Optimizadas

- **Códec Preferido**: H.264 (con aceleración de hardware OMX)
- **Resolución**: 1920x1080
- **Bitrate Recomendado**: 6-8 Mbps (optimizado para 512MB RAM)
- **Frame Rate**: 30 fps
- **Perfil H.264**: Main Profile
- **Contenedor**: MP4

#### Comando de Conversión Optimizado

```bash
# Conversión optimizada para Pi 3 A+
ffmpeg -i input.mp4 \
  -c:v h264_omx \
  -b:v 6M \
  -maxrate 8M \
  -bufsize 12M \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2" \
  -c:a aac \
  -b:a 128k \
  -movflags +faststart \
  output.mp4
```

## Configuración Avanzada de VLC

### Opciones de VLC para Modo Headless

#### Configuración Básica
```python
from pydantic import BaseModel, Field, validator
from typing import List

class VLCConfig(BaseModel):
    """Configuración de VLC optimizada para cartelería digital.
    
    Esta clase define las opciones de VLC con validación pydantic
    para garantizar configuraciones correctas del reproductor.
    """
    
    interface: str = Field(
        default='dummy',
        description="Interfaz de VLC (dummy para modo headless)"
    )
    fullscreen: bool = Field(
        default=True,
        description="Reproducción en pantalla completa"
    )
    show_video_title: bool = Field(
        default=False,
        description="Mostrar títulos en pantalla"
    )
    show_osd: bool = Field(
        default=False,
        description="Mostrar mensajes en pantalla (OSD)"
    )
    enable_subtitles: bool = Field(
        default=False,
        description="Habilitar subtítulos"
    )
    disable_screensaver: bool = Field(
        default=False,
        description="Desactivar protector de pantalla"
    )
    enable_loop: bool = Field(
        default=False,
        description="Bucle automático (controlado por aplicación)"
    )
    enable_audio: bool = Field(
        default=False,
        description="Habilitar audio"
    )
    quiet_mode: bool = Field(
        default=True,
        description="Modo silencioso"
    )
    show_stats: bool = Field(
        default=False,
        description="Mostrar estadísticas"
    )
    enable_file_caching: bool = Field(
        default=False,
        description="Habilitar caché de archivos"
    )
    
    def to_vlc_args(self) -> List[str]:
        """Convertir configuración a argumentos de VLC."""
        args = ['--intf', self.interface]
        
        if not self.show_video_title:
            args.append('--no-video-title-show')
        if self.fullscreen:
            args.append('--fullscreen')
        if not self.show_osd:
            args.append('--no-osd')
        if not self.enable_subtitles:
            args.append('--no-spu')
        if not self.disable_screensaver:
            args.append('--no-disable-screensaver')
        if not self.enable_loop:
            args.append('--no-loop')
        if not self.enable_audio:
            args.append('--no-audio')
        if self.quiet_mode:
            args.append('--quiet')
        if not self.show_stats:
            args.append('--no-stats')
        if not self.enable_file_caching:
            args.append('--no-file-caching')
            
        return args

# Configuración por defecto
VLC_OPTIONS = VLCConfig().to_vlc_args()
```

#### Configuración Específica para Pi 3 A+

```python
class VLCConfigPi3A(VLCConfig):
    """Configuración de VLC específica para Raspberry Pi 3 A+.
    
    Hereda de VLCConfig y añade optimizaciones específicas
    para el hardware del Pi 3 A+.
    """
    
    video_output: str = Field(
        default='mmal_vout',
        description="Salida de video optimizada para Pi 3 A+"
    )
    codec: str = Field(
        default='mmal',
        description="Códec de hardware OMX/MMAL"
    )
    
    def __init__(self, **data):
        # Configuración optimizada para Pi 3 A+
        pi3a_defaults = {
            'enable_audio': False,  # Desactivar audio para ahorrar RAM
            'enable_file_caching': False,  # Sin caché para refresh inmediato
            **data
        }
        super().__init__(**pi3a_defaults)
    
    def to_vlc_args(self) -> List[str]:
        """Convertir configuración a argumentos de VLC para Pi 3 A+."""
        args = super().to_vlc_args()
        args.extend(['--vout', self.video_output])
        args.extend(['--codec', self.codec])
        return args

# Configuración específica para Pi 3 A+
VLC_OPTIONS_PI3A = VLCConfigPi3A().to_vlc_args()
```

### Solución de Problemas de Pantalla Completa

Problema común: VLC no reproduce en pantalla completa correctamente. <mcreference link="https://stackoverflow.com/questions/77661453/why-is-python-vlc-playing-a-video-in-its-native-resolution-not-fullscreen-even" index="2">2</mcreference>

**Solución**:
```python
import vlc
import time

def create_fullscreen_player():
    # Crear instancia VLC con opciones específicas
    instance = vlc.Instance([
        '--intf', 'dummy',
        '--no-video-title-show',
        '--fullscreen',
        '--no-osd'
    ])
    
    player = instance.media_player_new()
    
    # Configurar pantalla completa después de crear el reproductor
    player.set_fullscreen(True)
    
    return player, instance

def play_video_fullscreen(video_path):
    player, instance = create_fullscreen_player()
    
    media = instance.media_new(video_path)
    player.set_media(media)
    
    player.play()
    
    # Esperar a que inicie la reproducción
    time.sleep(1)
    
    # Forzar pantalla completa nuevamente
    player.set_fullscreen(True)
    
    return player
```

## Monitoreo y Diagnóstico del Sistema

### Métricas de Rendimiento

#### Script de Monitoreo
```python
#!/usr/bin/env python3

import psutil
import subprocess
import json
from datetime import datetime

def get_system_metrics():
    """Obtener métricas del sistema para cartelería digital."""
    
    # CPU y memoria
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    
    # Temperatura (Raspberry Pi específico)
    try:
        temp_result = subprocess.run(
            ['vcgencmd', 'measure_temp'], 
            capture_output=True, text=True
        )
        temp = temp_result.stdout.strip().replace('temp=', '').replace("'C", '')
        temperature = float(temp)
    except:
        temperature = None
    
    # Memoria GPU
    try:
        gpu_mem_result = subprocess.run(
            ['vcgencmd', 'get_mem', 'gpu'], 
            capture_output=True, text=True
        )
        gpu_memory = gpu_mem_result.stdout.strip()
    except:
        gpu_memory = None
    
    # Procesos VLC
    vlc_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        if 'vlc' in proc.info['name'].lower():
            vlc_processes.append(proc.info)
    
    return {
        'timestamp': datetime.now().isoformat(),
        'cpu_percent': cpu_percent,
        'memory_percent': memory.percent,
        'memory_available_gb': memory.available / (1024**3),
        'temperature_celsius': temperature,
        'gpu_memory': gpu_memory,
        'vlc_processes': vlc_processes
    }

if __name__ == '__main__':
    metrics = get_system_metrics()
    print(json.dumps(metrics, indent=2))
```

### Alertas y Umbrales

```python
from pydantic import BaseModel, Field
from typing import Dict, List, Optional

class AlertThresholds(BaseModel):
    """Umbrales de alerta para monitoreo del sistema.
    
    Esta clase define los límites para generar alertas
    de rendimiento del sistema con validación pydantic.
    """
    
    cpu_percent: float = Field(
        default=80.0,
        ge=0.0,
        le=100.0,
        description="Umbral de uso de CPU en porcentaje"
    )
    memory_percent: float = Field(
        default=85.0,
        ge=0.0,
        le=100.0,
        description="Umbral de uso de memoria en porcentaje"
    )
    temperature_celsius: float = Field(
        default=70.0,
        ge=0.0,
        le=100.0,
        description="Umbral de temperatura en grados Celsius"
    )
    disk_usage_percent: float = Field(
        default=90.0,
        ge=0.0,
        le=100.0,
        description="Umbral de uso de disco en porcentaje"
    )
    
    def to_dict(self) -> Dict[str, float]:
        """Convertir a diccionario para compatibilidad."""
        return self.dict()

# Instancia de umbrales por defecto
ALERT_THRESHOLDS = AlertThresholds()

def check_system_health():
    """Verificar salud del sistema y generar alertas."""
    metrics = get_system_metrics()
    alerts = []
    
    if metrics['cpu_percent'] > ALERT_THRESHOLDS['cpu_percent']:
        alerts.append(f"Alto uso de CPU: {metrics['cpu_percent']:.1f}%")
    
    if metrics['memory_percent'] > ALERT_THRESHOLDS['memory_percent']:
        alerts.append(f"Alta uso de memoria: {metrics['memory_percent']:.1f}%")
    
    if metrics['temperature_celsius'] and metrics['temperature_celsius'] > ALERT_THRESHOLDS['temperature_celsius']:
        alerts.append(f"Temperatura alta: {metrics['temperature_celsius']:.1f}°C")
    
    return alerts
```

## Configuración de Red y Conectividad

### Configuración WiFi Optimizada

```bash
# /etc/wpa_supplicant/wpa_supplicant.conf optimizado
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=ES  # Ajustar según país

network={
    ssid="TU_WIFI"
    psk="TU_PASSWORD"
    scan_ssid=1
    priority=1
    
    # Optimizaciones para estabilidad
    proto=RSN
    key_mgmt=WPA-PSK
    pairwise=CCMP
    auth_alg=OPEN
}
```

### Configuración de Red Estática (Recomendado)

```bash
# /etc/dhcpcd.conf - IP estática para mayor estabilidad
interface wlan0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8
```

## Gestión de Contenido

### Estructura de Directorios Recomendada

```
/home/pi/kdx-pi-signage/
├── videos/
│   ├── active/          # Videos activos para reproducción
│   ├── staging/         # Videos en preparación
│   ├── archive/         # Videos archivados
│   └── temp/           # Archivos temporales
├── logs/
│   ├── application.log
│   ├── system.log
│   └── vlc.log
├── config/
│   ├── playlist.json
│   └── settings.json
└── scripts/
    ├── monitor.py
    ├── health_check.py
    └── backup.py
```

### Script de Gestión de Videos

```python
#!/usr/bin/env python3

import os
import shutil
from pathlib import Path
import hashlib

class VideoManagerConfig(BaseModel):
    """Configuración del gestor de videos con validación pydantic.
    
    Esta clase define las rutas y configuraciones del sistema
    de gestión de videos con validación robusta.
    """
    
    base_path: Path = Field(
        default=Path('/home/pi/kdx-pi-signage'),
        description="Ruta base del sistema"
    )
    videos_directory: str = Field(
        default='videos',
        description="Nombre del directorio de videos"
    )
    active_directory: str = Field(
        default='active',
        description="Directorio de videos activos"
    )
    staging_directory: str = Field(
        default='staging',
        description="Directorio de videos en preparación"
    )
    archive_directory: str = Field(
        default='archive',
        description="Directorio de videos archivados"
    )
    max_video_size_mb: int = Field(
        default=500,
        ge=1,
        description="Tamaño máximo de video en MB"
    )
    supported_formats: List[str] = Field(
        default=['.mp4', '.avi', '.mkv', '.mov'],
        description="Formatos de video soportados"
    )
    
    @property
    def videos_path(self) -> Path:
        """Ruta completa al directorio de videos."""
        return self.base_path / self.videos_directory
    
    @property
    def active_path(self) -> Path:
        """Ruta completa al directorio de videos activos."""
        return self.videos_path / self.active_directory
    
    @property
    def staging_path(self) -> Path:
        """Ruta completa al directorio de staging."""
        return self.videos_path / self.staging_directory
    
    @property
    def archive_path(self) -> Path:
        """Ruta completa al directorio de archivo."""
        return self.videos_path / self.archive_directory

class VideoManager:
    def __init__(self, config: Optional[VideoManagerConfig] = None):
        self.config = config or VideoManagerConfig()
        
        # Crear directorios si no existen
        for path in [self.config.active_path, self.config.staging_path, self.config.archive_path]:
            path.mkdir(parents=True, exist_ok=True)
    
    def validate_video(self, video_path):
        """Validar que el video cumple con los requisitos."""
        try:
            import cv2
            cap = cv2.VideoCapture(str(video_path))
            
            if not cap.isOpened():
                return False, "No se puede abrir el video"
            
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            cap.release()
            
            # Validaciones
            if width != 1920 or height != 1080:
                return False, f"Resolución incorrecta: {width}x{height} (requerido: 1920x1080)"
            
            if fps > 60:
                return False, f"FPS muy alto: {fps} (máximo recomendado: 60)"
            
            return True, "Video válido"
            
        except Exception as e:
            return False, f"Error al validar video: {str(e)}"
    
    def add_video(self, source_path, validate=True):
        """Agregar video al sistema."""
        source_path = Path(source_path)
        
        if not source_path.exists():
            return False, "Archivo no encontrado"
        
        if validate:
            is_valid, message = self.validate_video(source_path)
            if not is_valid:
                return False, message
        
        # Copiar a staging
        dest_path = self.staging_path / source_path.name
        shutil.copy2(source_path, dest_path)
        
        return True, f"Video agregado a staging: {dest_path}"
    
    def activate_video(self, video_name):
        """Mover video de staging a active."""
        staging_file = self.staging_path / video_name
        active_file = self.active_path / video_name
        
        if not staging_file.exists():
            return False, "Video no encontrado en staging"
        
        shutil.move(staging_file, active_file)
        return True, f"Video activado: {active_file}"
    
    def get_active_videos(self):
        """Obtener lista de videos activos."""
        return list(self.active_path.glob('*.mp4'))
```

## Sistema de Logging con Loguru

### Configuración de Loguru
- **Ubicación**: `/home/pi/kdx-pi-signage/logs/`
- **Rotación**: Archivos de máximo 10MB, retención 30 días
- **Compresión**: Archivos antiguos comprimidos en ZIP
- **Niveles**: INFO para operaciones, WARNING/ERROR para consola
- **Formato**: Timestamp, nivel, función:línea, mensaje

### Estructura de Logs
```
logs/
├── signage.log          # Log principal (INFO+)
├── errors.log           # Solo errores (ERROR+)
├── archived/            # Logs comprimidos
│   ├── signage.2024-01-01.zip
│   └── errors.2024-01-01.zip
└── current/             # Logs activos
```

### Patrones de Diseño en Logging
- **Singleton Pattern**: Una sola instancia del logger en todo el sistema
- **Observer Pattern**: Notificación automática de eventos críticos
- **Factory Pattern**: Creación de diferentes tipos de handlers según contexto

### Configuración de Logging con Loguru

```python
from loguru import logger
import os
import sys
from pathlib import Path
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any

class LoguruConfig(BaseModel):
    """Configuración de Loguru con validación pydantic.
    
    Esta clase define la configuración completa del sistema
    de logging con validación robusta de parámetros.
    """
    
    log_directory: Path = Field(
        default=Path('/home/pi/kdx-pi-signage/logs'),
        description="Directorio base para archivos de log"
    )
    console_level: str = Field(
        default="WARNING",
        description="Nivel mínimo para logs en consola"
    )
    file_level: str = Field(
        default="INFO",
        description="Nivel mínimo para logs en archivo"
    )
    error_level: str = Field(
        default="ERROR",
        description="Nivel mínimo para archivo de errores"
    )
    main_log_rotation: str = Field(
        default="10 MB",
        description="Tamaño de rotación para log principal"
    )
    error_log_rotation: str = Field(
        default="5 MB",
        description="Tamaño de rotación para log de errores"
    )
    retention_days: int = Field(
        default=30,
        ge=1,
        le=365,
        description="Días de retención para logs principales"
    )
    error_retention_days: int = Field(
        default=60,
        ge=1,
        le=365,
        description="Días de retención para logs de errores"
    )
    enable_compression: bool = Field(
        default=True,
        description="Habilitar compresión de logs antiguos"
    )
    enable_backtrace: bool = Field(
        default=True,
        description="Habilitar backtrace en errores"
    )
    enable_diagnose: bool = Field(
        default=True,
        description="Habilitar diagnóstico detallado"
    )
    
    @validator('console_level', 'file_level', 'error_level')
    def validate_log_levels(cls, v):
        """Validar que los niveles de log sean válidos."""
        valid_levels = ['TRACE', 'DEBUG', 'INFO', 'SUCCESS', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"Nivel de log inválido: {v}. Debe ser uno de: {valid_levels}")
        return v.upper()
    
    @validator('log_directory')
    def create_log_directory(cls, v):
        """Crear directorio de logs si no existe."""
        if isinstance(v, str):
            v = Path(v)
        v.mkdir(parents=True, exist_ok=True)
        return v

class LoguruManager:
    """Gestor singleton de Loguru con configuración pydantic."""
    
    _instance: Optional['LoguruManager'] = None
    _logger_configured: bool = False
    
    def __new__(cls, config: Optional[LoguruConfig] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Optional[LoguruConfig] = None):
        if not self._logger_configured:
            self.config = config or LoguruConfig()
            self._setup_logger()
            self._logger_configured = True
    
    def _setup_logger(self):
        """Configurar Loguru según la configuración pydantic."""
        # Remover handler por defecto
        logger.remove()
        
        # Handler para consola
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=self.config.console_level,
            colorize=True
        )
        
        # Handler para archivo principal
        logger.add(
            self.config.log_directory / "signage.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=self.config.file_level,
            rotation=self.config.main_log_rotation,
            retention=f"{self.config.retention_days} days",
            compression="zip" if self.config.enable_compression else None,
            enqueue=True
        )
        
        # Handler para errores
        logger.add(
            self.config.log_directory / "errors.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}\n{exception}",
            level=self.config.error_level,
            rotation=self.config.error_log_rotation,
            retention=f"{self.config.error_retention_days} days",
            compression="zip" if self.config.enable_compression else None,
            backtrace=self.config.enable_backtrace,
            diagnose=self.config.enable_diagnose
        )
    
    def get_logger(self):
        """Obtener instancia del logger configurado."""
        return logger

def setup_loguru_logging(config: Optional[LoguruConfig] = None):
    """Configurar sistema de logging con Loguru usando pydantic."""
    manager = LoguruManager(config)
    return manager.get_logger()

def get_logger(config: Optional[LoguruConfig] = None):
    """Obtener instancia singleton del logger."""
    return setup_loguru_logging(config)
```

Esta documentación complementaria proporciona las especificaciones técnicas detalladas y optimizaciones específicas para diferentes modelos de Raspberry Pi, asegurando el mejor rendimiento posible del sistema de cartelería digital.