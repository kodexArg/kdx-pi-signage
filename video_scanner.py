"""Escáner de directorio que busca archivos de video disponibles.

Este módulo implementa el patrón Observer para monitorear cambios
en el directorio de videos y actualizar automáticamente la playlist.
"""

import time
from pathlib import Path
from typing import List, Optional, Callable, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from logger import app_logger
from config import SystemConfig, DEFAULT_SYSTEM_CONFIG


class VideoFileHandler(FileSystemEventHandler):
    """Manejador de eventos del sistema de archivos para videos.
    
    Esta clase implementa el patrón Observer para detectar cambios
    en el directorio de videos y notificar al sistema principal.
    """
    
    def __init__(self, supported_formats: List[str], callback: Optional[Callable] = None):
        """Inicializa el manejador de eventos.
        
        Args:
            supported_formats: Lista de extensiones de video soportadas
            callback: Función a llamar cuando se detecten cambios
        """
        super().__init__()
        self.supported_formats = [fmt.lower() for fmt in supported_formats]
        self.callback = callback
        self.logger = app_logger.get_logger()
    
    def _is_video_file(self, file_path: str) -> bool:
        """Verifica si un archivo es un video soportado.
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            True si es un archivo de video soportado
        """
        return Path(file_path).suffix.lower() in self.supported_formats
    
    def on_created(self, event: FileSystemEvent) -> None:
        """Maneja eventos de creación de archivos.
        
        Args:
            event: Evento del sistema de archivos
        """
        if not event.is_directory and self._is_video_file(event.src_path):
            self.logger.info(f"Nuevo video detectado: {Path(event.src_path).name}")
            if self.callback:
                self.callback('created', event.src_path)
    
    def on_deleted(self, event: FileSystemEvent) -> None:
        """Maneja eventos de eliminación de archivos.
        
        Args:
            event: Evento del sistema de archivos
        """
        if not event.is_directory and self._is_video_file(event.src_path):
            self.logger.info(f"Video eliminado: {Path(event.src_path).name}")
            if self.callback:
                self.callback('deleted', event.src_path)
    
    def on_moved(self, event: FileSystemEvent) -> None:
        """Maneja eventos de movimiento/renombrado de archivos.
        
        Args:
            event: Evento del sistema de archivos
        """
        if hasattr(event, 'dest_path'):
            # Archivo movido/renombrado
            if not event.is_directory:
                src_is_video = self._is_video_file(event.src_path)
                dest_is_video = self._is_video_file(event.dest_path)
                
                if src_is_video and dest_is_video:
                    # Renombrado de video
                    self.logger.info(f"Video renombrado: {Path(event.src_path).name} -> {Path(event.dest_path).name}")
                    if self.callback:
                        self.callback('moved', event.src_path, event.dest_path)
                elif src_is_video and not dest_is_video:
                    # Video movido fuera o cambio de extensión
                    self.logger.info(f"Video removido: {Path(event.src_path).name}")
                    if self.callback:
                        self.callback('deleted', event.src_path)
                elif not src_is_video and dest_is_video:
                    # Archivo convertido a video
                    self.logger.info(f"Nuevo video: {Path(event.dest_path).name}")
                    if self.callback:
                        self.callback('created', event.dest_path)


class VideoScanner:
    """Escáner de directorio que busca archivos de video disponibles.
    
    Esta clase implementa el patrón Observer para monitorear cambios
    en el directorio de videos y proporcionar funcionalidades de escaneo.
    """
    
    def __init__(self, config: Optional[SystemConfig] = None):
        """Inicializa el escáner con la configuración especificada.
        
        Args:
            config: Configuración del sistema. Si es None, usa la configuración por defecto.
        """
        self.config = config or DEFAULT_SYSTEM_CONFIG
        self.logger = app_logger.get_logger()
        
        # Estado del escáner
        self._observer: Optional[Observer] = None
        self._is_monitoring = False
        self._last_scan_time: Optional[float] = None
        self._cached_videos: Set[str] = set()
        
        # Callbacks
        self._on_change_callback: Optional[Callable] = None
        
        self.logger.info(f"VideoScanner inicializado para directorio: {self.config.video_dir}")
    
    def scan_videos(self, directory_path: Optional[str] = None) -> List[str]:
        """Escanea el directorio y retorna lista de archivos de video.
        
        Args:
            directory_path: Ruta del directorio. Si es None, usa el directorio configurado.
            
        Returns:
            Lista de rutas completas de archivos de video
        """
        if directory_path is None:
            directory_path = str(self.config.video_dir)
        
        video_dir = Path(directory_path)
        video_files = []
        
        if not video_dir.exists():
            self.logger.warning(f"Directorio de videos no existe: {directory_path}")
            return video_files
        
        if not video_dir.is_dir():
            self.logger.error(f"La ruta no es un directorio: {directory_path}")
            return video_files
        
        try:
            # Buscar archivos de video
            for file_path in video_dir.iterdir():
                if (file_path.is_file() and 
                    file_path.suffix.lower() in self.config.supported_formats):
                    
                    # Verificar que el archivo sea accesible
                    try:
                        if file_path.stat().st_size > 0:  # Archivo no vacío
                            video_files.append(str(file_path))
                    except OSError as e:
                        self.logger.warning(f"No se puede acceder al archivo {file_path}: {e}")
            
            # Ordenar archivos por nombre
            video_files.sort()
            
            # Actualizar caché y timestamp
            self._cached_videos = set(video_files)
            self._last_scan_time = time.time()
            
            self.logger.info(f"Escaneo completado: {len(video_files)} videos encontrados")
            
        except Exception as e:
            self.logger.error(f"Error durante el escaneo de {directory_path}: {e}")
        
        return video_files
    
    def get_video_count(self, directory_path: Optional[str] = None) -> int:
        """Obtiene el número de videos en el directorio.
        
        Args:
            directory_path: Ruta del directorio. Si es None, usa el directorio configurado.
            
        Returns:
            Número de archivos de video encontrados
        """
        return len(self.scan_videos(directory_path))
    
    def refresh_playlist(self) -> List[str]:
        """Actualiza la lista de reproducción con videos encontrados.
        
        Returns:
            Lista actualizada de archivos de video
        """
        self.logger.info("Actualizando playlist...")
        return self.scan_videos()
    
    def start_monitoring(self, callback: Optional[Callable] = None) -> bool:
        """Inicia el monitoreo automático del directorio de videos.
        
        Args:
            callback: Función a llamar cuando se detecten cambios
            
        Returns:
            True si el monitoreo se inició correctamente
        """
        if self._is_monitoring:
            self.logger.warning("El monitoreo ya está activo")
            return True
        
        if not self.config.video_dir.exists():
            self.logger.error(f"No se puede monitorear directorio inexistente: {self.config.video_dir}")
            return False
        
        try:
            # Configurar callback
            if callback:
                self._on_change_callback = callback
            
            # Crear manejador de eventos
            event_handler = VideoFileHandler(
                supported_formats=self.config.supported_formats,
                callback=self._handle_file_change
            )
            
            # Crear y configurar observer
            self._observer = Observer()
            self._observer.schedule(
                event_handler,
                str(self.config.video_dir),
                recursive=False
            )
            
            # Iniciar monitoreo
            self._observer.start()
            self._is_monitoring = True
            
            self.logger.info(f"Monitoreo iniciado para: {self.config.video_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al iniciar monitoreo: {e}")
            return False
    
    def stop_monitoring(self) -> bool:
        """Detiene el monitoreo automático del directorio.
        
        Returns:
            True si el monitoreo se detuvo correctamente
        """
        if not self._is_monitoring:
            return True
        
        try:
            if self._observer:
                self._observer.stop()
                self._observer.join(timeout=5)
                self._observer = None
            
            self._is_monitoring = False
            self.logger.info("Monitoreo detenido")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al detener monitoreo: {e}")
            return False
    
    def _handle_file_change(self, event_type: str, *args) -> None:
        """Maneja los cambios detectados en el directorio.
        
        Args:
            event_type: Tipo de evento ('created', 'deleted', 'moved')
            *args: Argumentos adicionales del evento
        """
        try:
            # Esperar un momento para que el archivo se estabilice
            time.sleep(0.5)
            
            # Re-escanear directorio
            current_videos = set(self.scan_videos())
            
            # Detectar cambios
            added_videos = current_videos - self._cached_videos
            removed_videos = self._cached_videos - current_videos
            
            # Notificar cambios si hay callback
            if self._on_change_callback and (added_videos or removed_videos):
                self._on_change_callback({
                    'event_type': event_type,
                    'added': list(added_videos),
                    'removed': list(removed_videos),
                    'total_videos': len(current_videos)
                })
            
            # Actualizar caché
            self._cached_videos = current_videos
            
        except Exception as e:
            self.logger.error(f"Error al manejar cambio de archivo: {e}")
    
    def is_monitoring(self) -> bool:
        """Verifica si el monitoreo está activo.
        
        Returns:
            True si el monitoreo está activo
        """
        return self._is_monitoring
    
    def get_last_scan_time(self) -> Optional[float]:
        """Obtiene el timestamp del último escaneo.
        
        Returns:
            Timestamp del último escaneo o None si no se ha escaneado
        """
        return self._last_scan_time
    
    def get_directory_info(self) -> dict:
        """Obtiene información sobre el directorio monitoreado.
        
        Returns:
            Diccionario con información del directorio
        """
        video_dir = self.config.video_dir
        
        info = {
            'directory_path': str(video_dir),
            'exists': video_dir.exists(),
            'is_monitoring': self._is_monitoring,
            'last_scan_time': self._last_scan_time,
            'supported_formats': self.config.supported_formats,
            'cached_video_count': len(self._cached_videos)
        }
        
        if video_dir.exists():
            try:
                stat = video_dir.stat()
                info.update({
                    'directory_size': sum(f.stat().st_size for f in video_dir.iterdir() if f.is_file()),
                    'last_modified': stat.st_mtime,
                    'permissions': oct(stat.st_mode)[-3:]
                })
            except OSError:
                pass
        
        return info
    
    def validate_directory(self) -> bool:
        """Valida que el directorio de videos sea accesible.
        
        Returns:
            True si el directorio es válido y accesible
        """
        video_dir = self.config.video_dir
        
        if not video_dir.exists():
            self.logger.error(f"Directorio no existe: {video_dir}")
            return False
        
        if not video_dir.is_dir():
            self.logger.error(f"La ruta no es un directorio: {video_dir}")
            return False
        
        try:
            # Intentar listar el contenido
            list(video_dir.iterdir())
            return True
        except PermissionError:
            self.logger.error(f"Sin permisos para acceder al directorio: {video_dir}")
            return False
        except Exception as e:
            self.logger.error(f"Error al validar directorio {video_dir}: {e}")
            return False
    
    def cleanup(self) -> None:
        """Limpia los recursos del escáner."""
        self.stop_monitoring()
        self._cached_videos.clear()
        self.logger.info("Recursos del escáner liberados")
    
    def __del__(self):
        """Destructor que asegura la limpieza de recursos."""
        self.cleanup()