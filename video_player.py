"""Reproductor de video que utiliza VLC para mostrar contenido multimedia.

Este módulo implementa el patrón Adapter para integrar VLC Media Player
con el sistema de cartelería digital, proporcionando una interfaz
simplificada para la reproducción de videos.
"""

import vlc
import time
import threading
from typing import Optional, Callable
from pathlib import Path

from logger import app_logger
from config import VLCConfig, DEFAULT_VLC_CONFIG


class VideoPlayerError(Exception):
    """Excepción personalizada para errores del reproductor de video."""
    pass


class VideoPlayer:
    """Reproductor de video que utiliza VLC para mostrar contenido multimedia.
    
    Esta clase implementa el patrón Adapter para proporcionar una interfaz
    simplificada sobre VLC Media Player, optimizada para cartelería digital
    en Raspberry Pi 3 A+.
    """
    
    def __init__(self, config: Optional[VLCConfig] = None):
        """Inicializa el reproductor con la configuración especificada.
        
        Args:
            config: Configuración de VLC. Si es None, usa la configuración por defecto.
        """
        self.config = config or DEFAULT_VLC_CONFIG
        self.logger = app_logger.get_logger()
        
        # Estado del reproductor
        self._instance: Optional[vlc.Instance] = None
        self._player: Optional[vlc.MediaPlayer] = None
        self._current_media: Optional[vlc.Media] = None
        self._is_playing = False
        self._current_video_path: Optional[str] = None
        
        # Callbacks
        self._on_end_callback: Optional[Callable] = None
        self._on_error_callback: Optional[Callable] = None
        
        # Thread para monitoreo
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_monitoring = False
        
        self._initialize_vlc()
    
    def _initialize_vlc(self) -> None:
        """Inicializa la instancia de VLC con la configuración especificada."""
        try:
            vlc_args = self.config.to_vlc_args()
            self.logger.info(f"Inicializando VLC con argumentos: {vlc_args}")
            
            self._instance = vlc.Instance(vlc_args)
            self._player = self._instance.media_player_new()
            
            # Configurar callbacks de eventos
            self._setup_event_callbacks()
            
            self.logger.info("VLC inicializado correctamente")
            
        except Exception as e:
            error_msg = f"Error al inicializar VLC: {str(e)}"
            self.logger.error(error_msg)
            raise VideoPlayerError(error_msg)
    
    def _setup_event_callbacks(self) -> None:
        """Configura los callbacks de eventos de VLC."""
        if not self._player:
            return
        
        event_manager = self._player.event_manager()
        
        # Callback para fin de reproducción
        event_manager.event_attach(
            vlc.EventType.MediaPlayerEndReached,
            self._on_media_end
        )
        
        # Callback para errores
        event_manager.event_attach(
            vlc.EventType.MediaPlayerEncounteredError,
            self._on_media_error
        )
        
        # Callback para cambios de estado
        event_manager.event_attach(
            vlc.EventType.MediaPlayerPlaying,
            self._on_media_playing
        )
        
        event_manager.event_attach(
            vlc.EventType.MediaPlayerStopped,
            self._on_media_stopped
        )
    
    def _on_media_end(self, event) -> None:
        """Callback llamado cuando termina la reproducción de un video."""
        self.logger.info(f"Reproducción terminada: {self._current_video_path}")
        self._is_playing = False
        
        if self._on_end_callback:
            try:
                self._on_end_callback()
            except Exception as e:
                self.logger.error(f"Error en callback de fin de reproducción: {e}")
    
    def _on_media_error(self, event) -> None:
        """Callback llamado cuando ocurre un error en la reproducción."""
        self.logger.error(f"Error en reproducción: {self._current_video_path}")
        self._is_playing = False
        
        if self._on_error_callback:
            try:
                self._on_error_callback()
            except Exception as e:
                self.logger.error(f"Error en callback de error: {e}")
    
    def _on_media_playing(self, event) -> None:
        """Callback llamado cuando inicia la reproducción."""
        self.logger.info(f"Reproducción iniciada: {self._current_video_path}")
        self._is_playing = True
    
    def _on_media_stopped(self, event) -> None:
        """Callback llamado cuando se detiene la reproducción."""
        self.logger.info(f"Reproducción detenida: {self._current_video_path}")
        self._is_playing = False
    
    def play_video(self, video_path: str) -> bool:
        """Inicia la reproducción del video especificado.
        
        Args:
            video_path: Ruta completa al archivo de video
            
        Returns:
            True si la reproducción se inició correctamente, False en caso contrario
        """
        if not self._player or not self._instance:
            self.logger.error("Reproductor no inicializado")
            return False
        
        video_file = Path(video_path)
        if not video_file.exists():
            self.logger.error(f"Archivo de video no encontrado: {video_path}")
            return False
        
        try:
            # Detener reproducción actual si existe
            if self._is_playing:
                self.stop()
            
            # Crear nuevo media
            self._current_media = self._instance.media_new(str(video_file))
            self._player.set_media(self._current_media)
            self._current_video_path = video_path
            
            # Iniciar reproducción
            result = self._player.play()
            
            if result == 0:  # 0 indica éxito en VLC
                # Esperar un momento para que inicie la reproducción
                time.sleep(0.5)
                
                # Forzar pantalla completa
                if self.config.fullscreen:
                    self._player.set_fullscreen(True)
                
                self.logger.info(f"Reproducción iniciada exitosamente: {video_path}")
                return True
            else:
                self.logger.error(f"Error al iniciar reproducción: código {result}")
                return False
                
        except Exception as e:
            error_msg = f"Error al reproducir video {video_path}: {str(e)}"
            self.logger.error(error_msg)
            return False
    
    def stop(self) -> bool:
        """Detiene la reproducción actual del video.
        
        Returns:
            True si se detuvo correctamente, False en caso contrario
        """
        if not self._player:
            return False
        
        try:
            self._player.stop()
            self._is_playing = False
            self._current_video_path = None
            
            self.logger.info("Reproducción detenida")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al detener reproducción: {str(e)}")
            return False
    
    def pause(self) -> bool:
        """Pausa la reproducción actual.
        
        Returns:
            True si se pausó correctamente, False en caso contrario
        """
        if not self._player:
            return False
        
        try:
            self._player.pause()
            self.logger.info("Reproducción pausada")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al pausar reproducción: {str(e)}")
            return False
    
    def resume(self) -> bool:
        """Reanuda la reproducción pausada.
        
        Returns:
            True si se reanudó correctamente, False en caso contrario
        """
        if not self._player:
            return False
        
        try:
            self._player.play()
            self.logger.info("Reproducción reanudada")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al reanudar reproducción: {str(e)}")
            return False
    
    def is_playing(self) -> bool:
        """Verifica si hay un video reproduciéndose actualmente.
        
        Returns:
            True si hay un video reproduciéndose, False en caso contrario
        """
        if not self._player:
            return False
        
        # Verificar estado de VLC
        state = self._player.get_state()
        vlc_is_playing = state == vlc.State.Playing
        
        # Actualizar estado interno
        self._is_playing = vlc_is_playing
        
        return self._is_playing
    
    def get_current_video(self) -> Optional[str]:
        """Obtiene la ruta del video actualmente en reproducción.
        
        Returns:
            Ruta del video actual o None si no hay reproducción
        """
        return self._current_video_path if self._is_playing else None
    
    def get_position(self) -> float:
        """Obtiene la posición actual de reproducción.
        
        Returns:
            Posición como porcentaje (0.0 a 1.0)
        """
        if not self._player or not self._is_playing:
            return 0.0
        
        try:
            return self._player.get_position()
        except Exception:
            return 0.0
    
    def get_length(self) -> int:
        """Obtiene la duración total del video en milisegundos.
        
        Returns:
            Duración en milisegundos o 0 si no hay video
        """
        if not self._player or not self._is_playing:
            return 0
        
        try:
            return self._player.get_length()
        except Exception:
            return 0
    
    def set_on_end_callback(self, callback: Callable) -> None:
        """Establece el callback para cuando termina la reproducción.
        
        Args:
            callback: Función a llamar cuando termine la reproducción
        """
        self._on_end_callback = callback
    
    def set_on_error_callback(self, callback: Callable) -> None:
        """Establece el callback para cuando ocurre un error.
        
        Args:
            callback: Función a llamar cuando ocurra un error
        """
        self._on_error_callback = callback
    
    def cleanup(self) -> None:
        """Limpia los recursos del reproductor."""
        try:
            # Detener monitoreo
            self._stop_monitoring = True
            if self._monitor_thread and self._monitor_thread.is_alive():
                self._monitor_thread.join(timeout=2)
            
            # Detener reproducción
            if self._player:
                self._player.stop()
            
            # Liberar recursos
            if self._current_media:
                self._current_media.release()
            
            if self._player:
                self._player.release()
            
            if self._instance:
                self._instance.release()
            
            self.logger.info("Recursos del reproductor liberados")
            
        except Exception as e:
            self.logger.error(f"Error al limpiar recursos: {str(e)}")
    
    def __del__(self):
        """Destructor que asegura la limpieza de recursos."""
        self.cleanup()