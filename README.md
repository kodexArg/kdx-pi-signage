# KDX Pi Signage - Sistema de Cartelería Digital

## Descripción General

Sistema de cartelería digital optimizado para Raspberry Pi que permite la reproducción automática de contenido multimedia en pantallas. Diseñado específicamente para funcionar de manera autónoma con arranque automático y gestión inteligente de recursos.

## Características Principales

### 🎯 Funcionalidades Core
- **Reproducción Automática**: Inicio automático al encender el dispositivo
- **Gestión de Playlists**: Reproducción secuencial de videos con configuración flexible
- **Monitoreo del Sistema**: Supervisión en tiempo real de recursos y rendimiento
- **Validación de Contenido**: Verificación automática de formatos y calidad de video
- **Logging Avanzado**: Sistema de logs robusto con rotación y compresión automática

### 🏗️ Arquitectura y Patrones de Diseño
- **Domain-Driven Design (DDD)**: Arquitectura por capas con separación clara de responsabilidades
- **Singleton Pattern**: Gestión centralizada de logger y configuración
- **Observer Pattern**: Notificación de eventos del sistema
- **Strategy Pattern**: Diferentes estrategias de reproducción según hardware
- **Facade Pattern**: Interfaz simplificada para operaciones complejas
- **Adapter Pattern**: Adaptación entre diferentes reproductores multimedia

## Especificaciones Técnicas

### Hardware Soportado
- **Raspberry Pi 3 A+** (configuración optimizada)
- **Raspberry Pi 4** (configuración estándar)
- **Mínimo**: 1GB RAM, 16GB microSD
- **Recomendado**: 2GB+ RAM, 32GB+ microSD Clase 10

### Software y Dependencias
- **Sistema Operativo**: Raspberry Pi OS Lite (64-bit)
- **Runtime**: Python 3.11+
- **Reproductor**: VLC Media Player
- **Validación**: Pydantic v2
- **Logging**: Loguru
- **Monitoreo**: psutil
- **Procesamiento**: OpenCV, FFmpeg

### Formatos de Video Soportados
- **Resolución**: 1920x1080 (Full HD)
- **Formatos**: MP4 (H.264/H.265), AVI, MKV
- **Códecs**: H.264 (recomendado), H.265/HEVC
- **FPS**: Hasta 60fps (30fps recomendado para Pi 3 A+)

## Estructura del Proyecto

```
kdx-pi-signage/
├── src/                          # Código fuente principal
│   ├── core/                     # Lógica de negocio central
│   │   ├── video_player.py       # Reproductor de video
│   │   ├── playlist_manager.py   # Gestor de playlists
│   │   └── system_monitor.py     # Monitor del sistema
│   ├── config/                   # Configuraciones
│   │   ├── settings.py           # Configuración principal
│   │   └── hardware_profiles.py  # Perfiles de hardware
│   ├── utils/                    # Utilidades
│   │   ├── logger.py             # Configuración de Loguru
│   │   └── validators.py         # Validadores Pydantic
│   └── main.py                   # Punto de entrada
├── videos/                       # Directorio de contenido
│   ├── active/                   # Videos activos
│   ├── staging/                  # Videos en preparación
│   └── archive/                  # Videos archivados
├── logs/                         # Archivos de log
├── config/                       # Archivos de configuración
├── scripts/                      # Scripts de instalación
└── docs/                         # Documentación
```

## Instalación y Configuración

### Instalación Rápida

```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/kdx-pi-signage.git
cd kdx-pi-signage

# Ejecutar script de instalación
sudo chmod +x scripts/install.sh
sudo ./scripts/install.sh

# Configurar arranque automático
sudo systemctl enable kdx-signage
sudo systemctl start kdx-signage
```

### Configuración Manual

1. **Instalar dependencias del sistema**:
```bash
sudo apt update
sudo apt install python3-pip vlc ffmpeg
```

2. **Instalar dependencias Python**:
```bash
pip3 install -r requirements.txt
```

3. **Configurar auto-login** (opcional):
```bash
sudo raspi-config
# Boot Options > Desktop/CLI > Console Autologin
```

## Configuración con Pydantic

El sistema utiliza modelos Pydantic para validación robusta de configuraciones:

### Configuración Principal
```python
from pydantic import BaseModel, Field
from pathlib import Path

class SystemConfig(BaseModel):
    """Configuración principal del sistema."""
    
    video_directory: Path = Field(
        default=Path('/home/pi/kdx-pi-signage/videos/active'),
        description="Directorio de videos activos"
    )
    fullscreen: bool = Field(
        default=True,
        description="Reproducir en pantalla completa"
    )
    loop_playlist: bool = Field(
        default=True,
        description="Repetir playlist automáticamente"
    )
    hardware_profile: str = Field(
        default="pi3a",
        description="Perfil de hardware (pi3a, pi4, generic)"
    )
```

### Configuración de VLC
```python
class VLCConfig(BaseModel):
    """Configuración optimizada de VLC."""
    
    def to_vlc_args(self) -> List[str]:
        """Convertir configuración a argumentos de VLC."""
        return [
            '--intf', 'dummy',
            '--no-video-title-show',
            '--fullscreen',
            '--no-osd'
        ]
```

## Sistema de Logging con Loguru

### Configuración Automática
```python
from loguru import logger
from src.utils.logger import setup_loguru_logging

# Configuración automática
logger = setup_loguru_logging()

# Uso en el código
logger.info("Sistema iniciado correctamente")
logger.warning("Advertencia de rendimiento")
logger.error("Error en reproducción de video")
```

### Estructura de Logs
- **signage.log**: Log principal (INFO+)
- **errors.log**: Solo errores (ERROR+)
- **Rotación**: 10MB máximo por archivo
- **Retención**: 30 días para logs principales, 60 días para errores
- **Compresión**: Archivos antiguos en formato ZIP

## Uso del Sistema

### Agregar Videos
```bash
# Copiar videos al directorio staging
cp mi_video.mp4 /home/pi/kdx-pi-signage/videos/staging/

# Activar video (mover a active)
python3 -m src.utils.video_manager activate mi_video.mp4
```

### Monitoreo del Sistema
```bash
# Ver logs en tiempo real
tail -f /home/pi/kdx-pi-signage/logs/signage.log

# Verificar estado del servicio
sudo systemctl status kdx-signage

# Ver métricas del sistema
python3 -m src.core.system_monitor
```

### Comandos de Control
```bash
# Iniciar servicio
sudo systemctl start kdx-signage

# Detener servicio
sudo systemctl stop kdx-signage

# Reiniciar servicio
sudo systemctl restart kdx-signage

# Ver logs del servicio
journalctl -u kdx-signage -f
```

## Optimizaciones por Hardware

### Raspberry Pi 3 A+
- Resolución máxima: 1920x1080@30fps
- Códec recomendado: H.264
- GPU split: 128MB
- Configuración VLC optimizada para bajo consumo

### Raspberry Pi 4
- Resolución máxima: 1920x1080@60fps
- Soporte H.265/HEVC
- GPU split: 256MB
- Configuración VLC estándar

## Convenciones de Desarrollo

### Idioma
- **Código**: Inglés (variables, funciones, clases)
- **Documentación**: Castellano (docstrings, comentarios, markdown)
- **Logs**: Castellano para mensajes de usuario

### Estándares de Código
- **Validación**: Pydantic para todos los modelos de datos
- **Logging**: Loguru con configuración centralizada
- **Tipos**: Type hints obligatorios
- **Formato**: Black + isort para formateo automático

## Solución de Problemas

### Problemas Comunes

**Video no se reproduce**:
```bash
# Verificar formato
ffprobe mi_video.mp4

# Verificar logs
tail -n 50 /home/pi/kdx-pi-signage/logs/errors.log
```

**Alto uso de CPU**:
```bash
# Verificar procesos
htop

# Ajustar configuración VLC
# Editar config/vlc_config.json
```

**Problemas de arranque**:
```bash
# Verificar servicio
sudo systemctl status kdx-signage

# Ver logs de arranque
journalctl -u kdx-signage --since "10 minutes ago"
```

## Contribución

### Desarrollo Local
```bash
# Instalar dependencias de desarrollo
pip3 install -r requirements-dev.txt

# Ejecutar tests
pytest tests/

# Formatear código
black src/
isort src/
```

### Estructura de Commits
- `feat:` Nueva funcionalidad
- `fix:` Corrección de errores
- `docs:` Actualización de documentación
- `refactor:` Refactorización de código
- `test:` Adición o modificación de tests

## Licencia

Este proyecto está licenciado bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## Soporte

Para reportar problemas o solicitar funcionalidades:
- **Issues**: [GitHub Issues](https://github.com/tu-usuario/kdx-pi-signage/issues)
- **Documentación**: Ver carpeta `docs/`
- **Wiki**: [GitHub Wiki](https://github.com/tu-usuario/kdx-pi-signage/wiki)

---

**Desarrollado con ❤️ para Raspberry Pi**