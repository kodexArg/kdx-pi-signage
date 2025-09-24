"""Gestor de listas de reproducción para videos.

Este módulo implementa el patrón Strategy para gestionar diferentes
estrategias de reproducción de listas de videos en el sistema de
cartelería digital.
"""

import random
from abc import ABC, abstractmethod
from typing import List, Optional, Protocol
from pathlib import Path

from logger import app_logger
from config import VideoInfo, Playlist, SystemConfig, DEFAULT_SYSTEM_CONFIG


class PlaybackStrategy(ABC):
    """Estrategia abstracta para reproducción de playlist.
    
    Define la interfaz común para diferentes estrategias de reproducción
    utilizando el patrón Strategy.
    """
    
    @abstractmethod
    def get_next_video(self, playlist: Playlist) -> Optional[VideoInfo]:
        """Obtiene el siguiente video según la estrategia.
        
        Args:
            playlist: Lista de reproducción actual
            
        Returns:
            VideoInfo del siguiente video o None si no hay más videos
        """
        pass
    
    @abstractmethod
    def reset(self, playlist: Playlist) -> None:
        """Reinicia la estrategia de reproducción.
        
        Args:
            playlist: Lista de reproducción a reiniciar
        """
        pass


class SequentialStrategy(PlaybackStrategy):
    """Estrategia de reproducción secuencial.
    
    Reproduce los videos en orden secuencial, reiniciando al final
    si el bucle está habilitado.
    """
    
    def get_next_video(self, playlist: Playlist) -> Optional[VideoInfo]:
        """Obtiene el siguiente video en orden secuencial.
        
        Args:
            playlist: Lista de reproducción actual
            
        Returns:
            VideoInfo del siguiente video o None si no hay más videos
        """
        if not playlist.videos:
            return None
        
        # Si estamos al final y no hay bucle, retornar None
        if playlist.current_index >= len(playlist.videos) - 1 and not playlist.loop_enabled:
            return None
        
        # Avanzar al siguiente índice
        playlist.current_index = (playlist.current_index + 1) % len(playlist.videos)
        
        return playlist.videos[playlist.current_index]
    
    def reset(self, playlist: Playlist) -> None:
        """Reinicia la reproducción al primer video.
        
        Args:
            playlist: Lista de reproducción a reiniciar
        """
        playlist.current_index = 0


class ShuffleStrategy(PlaybackStrategy):
    """Estrategia de reproducción aleatoria.
    
    Reproduce los videos en orden aleatorio, evitando repetir
    el mismo video consecutivamente.
    """
    
    def __init__(self):
        """Inicializa la estrategia de reproducción aleatoria."""
        self._played_indices: List[int] = []
        self._last_index: Optional[int] = None
    
    def get_next_video(self, playlist: Playlist) -> Optional[VideoInfo]:
        """Obtiene el siguiente video de forma aleatoria.
        
        Args:
            playlist: Lista de reproducción actual
            
        Returns:
            VideoInfo del siguiente video o None si no hay más videos
        """
        if not playlist.videos:
            return None
        
        # Si solo hay un video, devolverlo
        if len(playlist.videos) == 1:
            playlist.current_index = 0
            return playlist.videos[0]
        
        # Si hemos reproducido todos los videos, reiniciar si hay bucle
        if len(self._played_indices) >= len(playlist.videos):
            if not playlist.loop_enabled:
                return None
            self._played_indices.clear()
        
        # Obtener índices disponibles (no reproducidos)
        available_indices = [
            i for i in range(len(playlist.videos))
            if i not in self._played_indices
        ]
        
        # Si el último video reproducido está en los disponibles, removerlo
        # para evitar repetición inmediata
        if self._last_index is not None and self._last_index in available_indices:
            if len(available_indices) > 1:  # Solo si hay más opciones
                available_indices.remove(self._last_index)
        
        # Seleccionar índice aleatorio
        if available_indices:
            selected_index = random.choice(available_indices)
            self._played_indices.append(selected_index)
            self._last_index = selected_index
            playlist.current_index = selected_index
            
            return playlist.videos[selected_index]
        
        return None
    
    def reset(self, playlist: Playlist) -> None:
        """Reinicia la estrategia de reproducción aleatoria.
        
        Args:
            playlist: Lista de reproducción a reiniciar
        """
        self._played_indices.clear()
        self._last_index = None
        playlist.current_index = 0


class PlaylistManager:
    """Gestor de listas de reproducción para videos.
    
    Esta clase implementa el patrón Strategy para gestionar diferentes
    estrategias de reproducción y mantener el estado de la playlist.
    """
    
    def __init__(self, config: Optional[SystemConfig] = None):
        """Inicializa el gestor de playlist.
        
        Args:
            config: Configuración del sistema. Si es None, usa la configuración por defecto.
        """
        self.config = config or DEFAULT_SYSTEM_CONFIG
        self.logger = app_logger.get_logger()
        
        # Estado de la playlist
        self._playlist = Playlist()
        
        # Estrategias de reproducción
        self._sequential_strategy = SequentialStrategy()
        self._shuffle_strategy = ShuffleStrategy()
        self._current_strategy = self._sequential_strategy
        
        self.logger.info("PlaylistManager inicializado")
    
    def load_videos_from_directory(self, directory_path: Optional[str] = None) -> int:
        """Carga videos desde un directorio específico.
        
        Args:
            directory_path: Ruta del directorio. Si es None, usa el directorio configurado.
            
        Returns:
            Número de videos cargados
        """
        if directory_path is None:
            directory_path = str(self.config.video_dir)
        
        video_dir = Path(directory_path)
        
        if not video_dir.exists():
            self.logger.warning(f"Directorio de videos no existe: {directory_path}")
            return 0
        
        videos = []
        video_count = 0
        
        try:
            # Buscar archivos de video en el directorio
            for file_path in video_dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in self.config.supported_formats:
                    try:
                        video_info = VideoInfo(
                            file_path=file_path,
                            filename=file_path.name,
                            file_size=file_path.stat().st_size,
                            format_extension=file_path.suffix.lower()
                        )
                        videos.append(video_info)
                        video_count += 1
                        self.logger.debug(f"Video cargado: {file_path.name}")
                    except Exception as e:
                        self.logger.warning(f"Error al cargar video {file_path}: {e}")
            
            # Ordenar videos por nombre para reproducción consistente
            videos.sort(key=lambda v: v.filename.lower())
            
            # Actualizar playlist
            self._playlist.videos = videos
            self._playlist.current_index = 0
            
            # Reiniciar estrategia actual
            self._current_strategy.reset(self._playlist)
            
            self.logger.info(f"Cargados {video_count} videos desde {directory_path}")
            
        except Exception as e:
            self.logger.error(f"Error al cargar videos desde {directory_path}: {e}")
            return 0
        
        return video_count
    
    def get_current_video(self) -> Optional[VideoInfo]:
        """Obtiene el video actual de la playlist.
        
        Returns:
            VideoInfo del video actual o None si no hay videos
        """
        return self._playlist.get_current_video()
    
    def get_next_video(self) -> Optional[VideoInfo]:
        """Obtiene el siguiente video según la estrategia actual.
        
        Returns:
            VideoInfo del siguiente video o None si no hay más videos
        """
        return self._current_strategy.get_next_video(self._playlist)
    
    def set_shuffle_mode(self, enabled: bool) -> None:
        """Habilita o deshabilita el modo aleatorio.
        
        Args:
            enabled: True para habilitar modo aleatorio, False para secuencial
        """
        self._playlist.shuffle_enabled = enabled
        
        if enabled:
            self._current_strategy = self._shuffle_strategy
            self.logger.info("Modo aleatorio habilitado")
        else:
            self._current_strategy = self._sequential_strategy
            self.logger.info("Modo secuencial habilitado")
        
        # Reiniciar estrategia
        self._current_strategy.reset(self._playlist)
    
    def set_loop_mode(self, enabled: bool) -> None:
        """Habilita o deshabilita el bucle de reproducción.
        
        Args:
            enabled: True para habilitar bucle, False para reproducir una vez
        """
        self._playlist.loop_enabled = enabled
        
        if enabled:
            self.logger.info("Modo bucle habilitado")
        else:
            self.logger.info("Modo bucle deshabilitado")
    
    def reset_playlist(self) -> None:
        """Reinicia la playlist al primer video."""
        self._current_strategy.reset(self._playlist)
        self.logger.info("Playlist reiniciada")
    
    def get_playlist_info(self) -> dict:
        """Obtiene información sobre la playlist actual.
        
        Returns:
            Diccionario con información de la playlist
        """
        return {
            'total_videos': len(self._playlist.videos),
            'current_index': self._playlist.current_index,
            'shuffle_enabled': self._playlist.shuffle_enabled,
            'loop_enabled': self._playlist.loop_enabled,
            'is_empty': self._playlist.is_empty(),
            'current_video': self._playlist.get_current_video().filename if self._playlist.get_current_video() else None
        }
    
    def add_video(self, video_path: str) -> bool:
        """Añade un video individual a la playlist.
        
        Args:
            video_path: Ruta del archivo de video
            
        Returns:
            True si se añadió correctamente, False en caso contrario
        """
        try:
            video_file = Path(video_path)
            
            if not video_file.exists():
                self.logger.error(f"Archivo de video no encontrado: {video_path}")
                return False
            
            if video_file.suffix.lower() not in self.config.supported_formats:
                self.logger.error(f"Formato de video no soportado: {video_file.suffix}")
                return False
            
            video_info = VideoInfo(file_path=video_file)
            self._playlist.videos.append(video_info)
            
            self.logger.info(f"Video añadido a la playlist: {video_file.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al añadir video {video_path}: {e}")
            return False
    
    def remove_video(self, video_path: str) -> bool:
        """Remueve un video de la playlist.
        
        Args:
            video_path: Ruta del archivo de video a remover
            
        Returns:
            True si se removió correctamente, False en caso contrario
        """
        try:
            video_file = Path(video_path)
            
            # Buscar el video en la playlist
            for i, video_info in enumerate(self._playlist.videos):
                if video_info.file_path == video_file:
                    # Ajustar índice actual si es necesario
                    if i < self._playlist.current_index:
                        self._playlist.current_index -= 1
                    elif i == self._playlist.current_index:
                        # Si removemos el video actual, reiniciar
                        self._playlist.current_index = 0
                    
                    # Remover video
                    self._playlist.videos.pop(i)
                    
                    self.logger.info(f"Video removido de la playlist: {video_file.name}")
                    return True
            
            self.logger.warning(f"Video no encontrado en la playlist: {video_path}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error al remover video {video_path}: {e}")
            return False
    
    def clear_playlist(self) -> None:
        """Limpia completamente la playlist."""
        self._playlist.videos.clear()
        self._playlist.current_index = 0
        self._current_strategy.reset(self._playlist)
        
        self.logger.info("Playlist limpiada")
    
    def is_empty(self) -> bool:
        """Verifica si la playlist está vacía.
        
        Returns:
            True si no hay videos en la playlist
        """
        return self._playlist.is_empty()
    
    def get_video_count(self) -> int:
        """Obtiene el número total de videos en la playlist.
        
        Returns:
            Número de videos en la playlist
        """
        return len(self._playlist.videos)
    
    def get_video_list(self) -> List[str]:
        """Obtiene una lista con los nombres de todos los videos.
        
        Returns:
            Lista de nombres de archivos de video
        """
        return [video.filename for video in self._playlist.videos]