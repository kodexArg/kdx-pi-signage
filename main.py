"""Sistema de Cartelería Digital para Raspberry Pi 3 A+.

Este es el módulo principal que coordina todos los componentes del sistema
de cartelería digital, implementando el patrón Facade para simplificar
la interacción entre los diferentes subsistemas.
"""

import sys
import time
import signal
import threading
from pathlib import Path
from typing import Optional

from logger import app_logger
from config import SystemConfig, DEFAULT_SYSTEM_CONFIG
from video_player import VideoPlayer, VideoPlayerError
from playlist_manager import PlaylistManager
from video_scanner import VideoScanner


class SignageSystem:
    """Sistema principal de cartelería digital.
    
    Esta clase implementa el patrón Facade para coordinar todos los
    componentes del sistema y proporcionar una interfaz unificada.
    """
    
    def __init__(self, config: Optional[SystemConfig] = None):
        """Inicializa el sistema de cartelería.
        
        Args:
            config: Configuración del sistema. Si es None, usa la configuración por defecto.
        """
        self.config = config or DEFAULT_SYSTEM_CONFIG
        self.logger = app_logger.get_logger()
        
        # Componentes del sistema
        self.video_player: Optional[VideoPlayer] = None
        self.playlist_manager: Optional[PlaylistManager] = None
        self.video_scanner: Optional[VideoScanner] = None
        
        # Estado del sistema
        self._running = False
        self._main_thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()
        
        # Contadores de error
        self._error_count = 0
        self._consecutive_errors = 0
        
        self.logger.info("Sistema de cartelería inicializado")
    
    def initialize(self) -> bool:
        """Inicializa todos los componentes del sistema.
        
        Returns:
            True si la inicialización fue exitosa
        """
        try:
            self.logger.info("Inicializando componentes del sistema...")
            
            # Verificar directorio de videos
            if not self.config.video_dir.exists():
                self.logger.warning(f"Creando directorio de videos: {self.config.video_dir}")
                self.config.video_dir.mkdir(parents=True, exist_ok=True)
            
            # Inicializar escáner de videos
            self.video_scanner = VideoScanner(self.config)
            if not self.video_scanner.validate_directory():
                self.logger.error("Directorio de videos no válido")
                return False
            
            # Inicializar gestor de playlist
            self.playlist_manager = PlaylistManager(self.config)
            
            # Cargar videos iniciales
            video_count = self.playlist_manager.load_videos_from_directory()
            if video_count == 0:
                self.logger.warning("No se encontraron videos en el directorio")
            else:
                self.logger.info(f"Cargados {video_count} videos")
            
            # Inicializar reproductor de video
            self.video_player = VideoPlayer()
            
            # Configurar callbacks
            self.video_player.set_on_end_callback(self._on_video_end)
            self.video_player.set_on_error_callback(self._on_video_error)
            
            # Iniciar monitoreo de directorio
            self.video_scanner.start_monitoring(self._on_directory_change)
            
            self.logger.info("Todos los componentes inicializados correctamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error durante la inicialización: {e}")
            return False
    
    def start(self) -> bool:
        """Inicia el sistema de cartelería.
        
        Returns:
            True si el sistema se inició correctamente
        """
        if self._running:
            self.logger.warning("El sistema ya está ejecutándose")
            return True
        
        if not self.initialize():
            self.logger.error("Fallo en la inicialización del sistema")
            return False
        
        try:
            self._running = True
            self._shutdown_event.clear()
            
            # Iniciar hilo principal
            self._main_thread = threading.Thread(target=self._main_loop, daemon=False)
            self._main_thread.start()
            
            self.logger.info("Sistema de cartelería iniciado")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al iniciar el sistema: {e}")
            self._running = False
            return False
    
    def stop(self) -> None:
        """Detiene el sistema de cartelería."""
        if not self._running:
            return
        
        self.logger.info("Deteniendo sistema de cartelería...")
        
        # Señalar parada
        self._running = False
        self._shutdown_event.set()
        
        # Esperar a que termine el hilo principal
        if self._main_thread and self._main_thread.is_alive():
            self._main_thread.join(timeout=10)
        
        # Limpiar componentes
        self._cleanup()
        
        self.logger.info("Sistema de cartelería detenido")
    
    def _main_loop(self) -> None:
        """Bucle principal del sistema de cartelería."""
        self.logger.info("Iniciando bucle principal de reproducción")
        
        while self._running and not self._shutdown_event.is_set():
            try:
                # Verificar si hay videos disponibles
                if self.playlist_manager.is_empty():
                    self.logger.warning("No hay videos disponibles, esperando...")
                    self._wait_or_shutdown(5)
                    continue
                
                # Obtener siguiente video
                current_video = self.playlist_manager.get_current_video()
                if not current_video:
                    self.logger.warning("No se pudo obtener video actual")
                    self._wait_or_shutdown(2)
                    continue
                
                # Reproducir video
                self.logger.info(f"Reproduciendo: {current_video.filename}")
                
                if self.video_player.play_video(str(current_video.file_path)):
                    # Resetear contador de errores consecutivos
                    self._consecutive_errors = 0
                    
                    # Esperar a que termine la reproducción
                    self._wait_for_video_end()
                    
                    # Avanzar al siguiente video
                    next_video = self.playlist_manager.get_next_video()
                    if not next_video and not self.playlist_manager._playlist.loop_enabled:
                        self.logger.info("Playlist completada sin bucle, re-escaneando...")
                        self._refresh_playlist()
                
                else:
                    self.logger.error(f"Error al reproducir video: {current_video.filename}")
                    self._handle_playback_error()
                
            except Exception as e:
                self.logger.error(f"Error en bucle principal: {e}")
                self._handle_playback_error()
        
        self.logger.info("Bucle principal terminado")
    
    def _wait_for_video_end(self) -> None:
        """Espera a que termine la reproducción del video actual."""
        while (self._running and 
               not self._shutdown_event.is_set() and 
               self.video_player.is_playing()):
            
            self._wait_or_shutdown(1)
    
    def _wait_or_shutdown(self, seconds: float) -> bool:
        """Espera el tiempo especificado o hasta que se señale la parada.
        
        Args:
            seconds: Tiempo a esperar en segundos
            
        Returns:
            True si se completó la espera, False si se señaló parada
        """
        return not self._shutdown_event.wait(seconds)
    
    def _on_video_end(self) -> None:
        """Callback llamado cuando termina la reproducción de un video."""
        self.logger.debug("Video terminado, continuando con siguiente")
    
    def _on_video_error(self) -> None:
        """Callback llamado cuando ocurre un error en la reproducción."""
        self.logger.error("Error en reproducción de video")
        self._handle_playback_error()
    
    def _on_directory_change(self, change_info: dict) -> None:
        """Callback llamado cuando cambia el contenido del directorio.
        
        Args:
            change_info: Información sobre los cambios detectados
        """
        self.logger.info(f"Cambios detectados en directorio: {change_info}")
        
        # Programar actualización de playlist
        threading.Thread(target=self._refresh_playlist, daemon=True).start()
    
    def _refresh_playlist(self) -> None:
        """Actualiza la playlist con los videos actuales del directorio."""
        try:
            self.logger.info("Actualizando playlist...")
            
            # Recargar videos
            video_count = self.playlist_manager.load_videos_from_directory()
            
            if video_count == 0:
                self.logger.warning("No se encontraron videos después de la actualización")
            else:
                self.logger.info(f"Playlist actualizada con {video_count} videos")
            
        except Exception as e:
            self.logger.error(f"Error al actualizar playlist: {e}")
    
    def _handle_playback_error(self) -> None:
        """Maneja errores de reproducción."""
        self._error_count += 1
        self._consecutive_errors += 1
        
        self.logger.warning(f"Error de reproducción #{self._consecutive_errors}")
        
        # Si hay muchos errores consecutivos, re-escanear
        if self._consecutive_errors >= self.config.max_retries:
            self.logger.warning("Demasiados errores consecutivos, re-escaneando directorio")
            self._refresh_playlist()
            self._consecutive_errors = 0
        
        # Esperar antes de continuar
        self._wait_or_shutdown(self.config.retry_delay)
    
    def _cleanup(self) -> None:
        """Limpia todos los recursos del sistema."""
        try:
            if self.video_player:
                self.video_player.cleanup()
            
            if self.video_scanner:
                self.video_scanner.cleanup()
            
            self.logger.info("Recursos del sistema liberados")
            
        except Exception as e:
            self.logger.error(f"Error durante la limpieza: {e}")
    
    def get_system_status(self) -> dict:
        """Obtiene el estado actual del sistema.
        
        Returns:
            Diccionario con información del estado del sistema
        """
        status = {
            'running': self._running,
            'error_count': self._error_count,
            'consecutive_errors': self._consecutive_errors,
            'current_video': None,
            'playlist_info': {},
            'directory_info': {}
        }
        
        if self.video_player:
            status['current_video'] = self.video_player.get_current_video()
            status['is_playing'] = self.video_player.is_playing()
        
        if self.playlist_manager:
            status['playlist_info'] = self.playlist_manager.get_playlist_info()
        
        if self.video_scanner:
            status['directory_info'] = self.video_scanner.get_directory_info()
        
        return status


# Variable global para el sistema
signage_system: Optional[SignageSystem] = None


def signal_handler(signum, frame):
    """Manejador de señales del sistema.
    
    Args:
        signum: Número de señal
        frame: Frame actual
    """
    global signage_system
    
    logger = app_logger.get_logger()
    logger.info(f"Señal recibida: {signum}")
    
    if signage_system:
        signage_system.stop()
    
    sys.exit(0)


def main():
    """Función principal del sistema de cartelería digital."""
    global signage_system
    
    # Configurar logging
    app_logger.setup_logger()
    logger = app_logger.get_logger()
    
    logger.info("=== Iniciando Sistema de Cartelería Digital KDX ===")
    logger.info("Versión: 1.0.0")
    logger.info("Hardware: Raspberry Pi 3 A+")
    
    try:
        # Configurar manejadores de señales
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Crear y configurar sistema
        config = DEFAULT_SYSTEM_CONFIG
        signage_system = SignageSystem(config)
        
        # Iniciar sistema
        if not signage_system.start():
            logger.error("No se pudo iniciar el sistema")
            sys.exit(1)
        
        # Mantener el programa ejecutándose
        try:
            while signage_system._running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Interrupción por teclado recibida")
        
    except Exception as e:
        logger.error(f"Error crítico en el sistema: {e}")
        sys.exit(1)
    
    finally:
        if signage_system:
            signage_system.stop()
        
        logger.info("=== Sistema de Cartelería Digital Terminado ===")


if __name__ == "__main__":
    main()
