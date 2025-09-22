"""Modelos de configuración con validación Pydantic.

Este módulo define las estructuras de datos y configuraciones del sistema
de cartelería digital utilizando Pydantic para validación robusta.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from pathlib import Path
import os


class SystemConfig(BaseModel):
    """Configuración principal del sistema de cartelería digital.
    
    Esta clase centraliza toda la configuración del sistema usando
    modelos pydantic para validación robusta.
    """
    
    video_dir: Path = Field(
        default=Path('/home/pi/kdx-pi-signage/videos'),
        description="Directorio donde se almacenan los videos"
    )
    log_dir: Path = Field(
        default=Path('/home/pi/kdx-pi-signage/logs'),
        description="Directorio para archivos de log"
    )
    supported_formats: List[str] = Field(
        default=['.mp4', '.avi', '.mkv', '.mov', '.wmv'],
        description="Formatos de video soportados"
    )
    refresh_interval: int = Field(
        default=30,
        ge=5,
        le=300,
        description="Intervalo de actualización en segundos"
    )
    max_retries: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Número máximo de reintentos en caso de error"
    )
    retry_delay: int = Field(
        default=5,
        ge=1,
        le=60,
        description="Delay entre reintentos en segundos"
    )
    
    @validator('video_dir', 'log_dir')
    def validate_directories(cls, v):
        """Valida que los directorios existan o puedan crearse."""
        if isinstance(v, str):
            v = Path(v)
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    @validator('supported_formats')
    def validate_formats(cls, v):
        """Valida que los formatos tengan el formato correcto."""
        for fmt in v:
            if not fmt.startswith('.'):
                raise ValueError(f"Formato debe comenzar con punto: {fmt}")
        return v


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
    enable_audio: bool = Field(
        default=False,
        description="Habilitar audio"
    )
    quiet_mode: bool = Field(
        default=True,
        description="Modo silencioso"
    )
    video_output: str = Field(
        default='mmal_vout',
        description="Salida de video optimizada para Pi 3 A+"
    )
    codec: str = Field(
        default='mmal',
        description="Códec de hardware OMX/MMAL"
    )
    
    def to_vlc_args(self) -> List[str]:
        """Convertir configuración a argumentos de VLC.
        
        Returns:
            Lista de argumentos para VLC
        """
        args = ['--intf', self.interface]
        
        if not self.show_video_title:
            args.append('--no-video-title-show')
        if self.fullscreen:
            args.append('--fullscreen')
        if not self.show_osd:
            args.append('--no-osd')
        if not self.enable_subtitles:
            args.append('--no-spu')
        if not self.enable_audio:
            args.append('--no-audio')
        if self.quiet_mode:
            args.append('--quiet')
        
        # Configuración específica para Pi 3 A+
        args.extend(['--vout', self.video_output])
        args.extend(['--codec', self.codec])
            
        return args


class PlayerState(BaseModel):
    """Estado actual del reproductor de video.
    
    Esta clase mantiene el estado del reproductor y la playlist
    con validación de datos.
    """
    
    current_video: Optional[str] = Field(
        default=None,
        description="Ruta del video actualmente en reproducción"
    )
    is_playing: bool = Field(
        default=False,
        description="Indica si hay un video reproduciéndose"
    )
    playlist_index: int = Field(
        default=0,
        ge=0,
        description="Índice actual en la lista de reproducción"
    )
    total_videos: int = Field(
        default=0,
        ge=0,
        description="Total de videos en la playlist"
    )
    playback_errors: int = Field(
        default=0,
        ge=0,
        description="Contador de errores de reproducción"
    )
    last_scan_time: Optional[float] = Field(
        default=None,
        description="Timestamp del último escaneo de videos"
    )
    
    @validator('current_video')
    def validate_video_path(cls, v):
        """Valida que el archivo de video exista si se especifica."""
        if v is not None and not Path(v).exists():
            raise ValueError(f"Archivo de video no encontrado: {v}")
        return v


class VideoInfo(BaseModel):
    """Información detallada de un archivo de video.
    
    Esta clase encapsula los metadatos de un archivo de video
    con validación de existencia y formato.
    """
    
    file_path: Path = Field(description="Ruta completa del archivo")
    filename: str = Field(description="Nombre del archivo")
    file_size: int = Field(ge=0, description="Tamaño del archivo en bytes")
    format_extension: str = Field(description="Extensión del formato")
    is_valid: bool = Field(default=True, description="Indica si el archivo es válido")
    last_modified: Optional[float] = Field(
        default=None,
        description="Timestamp de última modificación"
    )
    
    @validator('file_path')
    def validate_file_exists(cls, v):
        """Valida que el archivo exista."""
        if isinstance(v, str):
            v = Path(v)
        if not v.exists():
            raise ValueError(f"Archivo no encontrado: {v}")
        return v
    
    @validator('filename', pre=True, always=True)
    def extract_filename(cls, v, values):
        """Extrae el nombre del archivo de la ruta."""
        if 'file_path' in values and values['file_path']:
            return values['file_path'].name
        return v
    
    @validator('format_extension', pre=True, always=True)
    def extract_extension(cls, v, values):
        """Extrae la extensión del archivo."""
        if 'file_path' in values and values['file_path']:
            return values['file_path'].suffix.lower()
        return v.lower() if v else ''
    
    @validator('file_size', pre=True, always=True)
    def get_file_size(cls, v, values):
        """Obtiene el tamaño del archivo."""
        if 'file_path' in values and values['file_path']:
            try:
                return values['file_path'].stat().st_size
            except OSError:
                return 0
        return v
    
    @validator('last_modified', pre=True, always=True)
    def get_last_modified(cls, v, values):
        """Obtiene el timestamp de última modificación."""
        if 'file_path' in values and values['file_path']:
            try:
                return values['file_path'].stat().st_mtime
            except OSError:
                return None
        return v


class Playlist(BaseModel):
    """Lista de reproducción de videos con metadatos.
    
    Esta clase gestiona la lista de reproducción con validación
    y métodos para navegación.
    """
    
    videos: List[VideoInfo] = Field(
        default_factory=list,
        description="Lista de videos en la playlist"
    )
    current_index: int = Field(
        default=0,
        ge=0,
        description="Índice del video actual"
    )
    shuffle_enabled: bool = Field(
        default=False,
        description="Indica si la reproducción aleatoria está activa"
    )
    loop_enabled: bool = Field(
        default=True,
        description="Indica si la playlist se repite al finalizar"
    )
    
    @validator('current_index')
    def validate_index(cls, v, values):
        """Valida que el índice esté dentro del rango válido."""
        if 'videos' in values and values['videos']:
            if v >= len(values['videos']):
                return 0  # Reset al inicio si está fuera de rango
        return v
    
    def get_current_video(self) -> Optional[VideoInfo]:
        """Obtiene el video actual de la playlist.
        
        Returns:
            VideoInfo del video actual o None si no hay videos
        """
        if self.videos and 0 <= self.current_index < len(self.videos):
            return self.videos[self.current_index]
        return None
    
    def get_next_video(self) -> Optional[VideoInfo]:
        """Obtiene el siguiente video en la playlist.
        
        Returns:
            VideoInfo del siguiente video o None si no hay más videos
        """
        if not self.videos:
            return None
        
        next_index = (self.current_index + 1) % len(self.videos)
        if next_index == 0 and not self.loop_enabled:
            return None
        
        self.current_index = next_index
        return self.videos[self.current_index]
    
    def reset_playlist(self) -> None:
        """Reinicia la playlist al primer video."""
        self.current_index = 0
    
    def is_empty(self) -> bool:
        """Verifica si la playlist está vacía.
        
        Returns:
            True si no hay videos en la playlist
        """
        return len(self.videos) == 0


# Configuración por defecto del sistema
DEFAULT_SYSTEM_CONFIG = SystemConfig()
DEFAULT_VLC_CONFIG = VLCConfig()