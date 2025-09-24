"""Tests unitarios para PlaylistManager."""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from playlist_manager import PlaylistManager, SequentialStrategy, ShuffleStrategy
from config import VideoInfo, Playlist


class TestSequentialStrategy:
    """Tests para SequentialStrategy."""
    
    def test_get_next_video_empty_playlist(self):
        """Test obtener siguiente video con playlist vacía."""
        strategy = SequentialStrategy()
        playlist = Playlist(videos=[], current_index=0, loop_enabled=True)
        
        result = strategy.get_next_video(playlist)
        
        assert result is None
    
    def test_get_next_video_with_loop(self, sample_video_info):
        """Test obtener siguiente video con bucle habilitado."""
        strategy = SequentialStrategy()
        playlist = Playlist(
            videos=sample_video_info,
            current_index=len(sample_video_info) - 1,  # Último video
            loop_enabled=True
        )
        
        result = strategy.get_next_video(playlist)
        
        assert result is not None
        assert result == sample_video_info[0]  # Debe volver al primero
        assert playlist.current_index == 0
    
    def test_get_next_video_without_loop(self, sample_video_info):
        """Test obtener siguiente video sin bucle."""
        strategy = SequentialStrategy()
        playlist = Playlist(
            videos=sample_video_info,
            current_index=len(sample_video_info) - 1,  # Último video
            loop_enabled=False
        )
        
        result = strategy.get_next_video(playlist)
        
        assert result is None
    
    def test_get_next_video_normal_sequence(self, sample_video_info):
        """Test obtener siguiente video en secuencia normal."""
        strategy = SequentialStrategy()
        playlist = Playlist(
            videos=sample_video_info,
            current_index=0,
            loop_enabled=True
        )
        
        result = strategy.get_next_video(playlist)
        
        assert result is not None
        assert result == sample_video_info[1]
        assert playlist.current_index == 1
    
    def test_reset(self, sample_playlist):
        """Test reset de estrategia secuencial."""
        strategy = SequentialStrategy()
        sample_playlist.current_index = 2
        
        strategy.reset(sample_playlist)
        
        assert sample_playlist.current_index == 0


class TestShuffleStrategy:
    """Tests para ShuffleStrategy."""
    
    def test_get_next_video_empty_playlist(self):
        """Test obtener siguiente video con playlist vacía."""
        strategy = ShuffleStrategy()
        playlist = Playlist(videos=[], current_index=0, loop_enabled=True)
        
        result = strategy.get_next_video(playlist)
        
        assert result is None
    
    @patch('random.choice')
    def test_get_next_video_random_selection(self, mock_choice, sample_video_info):
        """Test selección aleatoria de video."""
        strategy = ShuffleStrategy()
        playlist = Playlist(
            videos=sample_video_info,
            current_index=0,
            loop_enabled=True
        )
        
        # Mock para que siempre seleccione el segundo video
        mock_choice.return_value = 1
        
        result = strategy.get_next_video(playlist)
        
        assert result == sample_video_info[1]
        assert playlist.current_index == 1
        mock_choice.assert_called_once()
    
    def test_reset(self, sample_playlist):
        """Test reset de estrategia shuffle."""
        strategy = ShuffleStrategy()
        strategy._played_indices = [0, 1]
        strategy._last_index = 1
        sample_playlist.current_index = 2
        
        strategy.reset(sample_playlist)
        
        assert sample_playlist.current_index == 0
        assert strategy._played_indices == []
        assert strategy._last_index is None


class TestPlaylistManager:
    """Tests para PlaylistManager."""
    
    def test_init_with_default_strategy(self, test_config):
        """Test inicialización con estrategia por defecto."""
        manager = PlaylistManager(test_config)
        
        assert manager.config == test_config
        assert isinstance(manager._current_strategy, SequentialStrategy)
        assert manager._playlist is not None
        assert manager._playlist.videos == []
    
    def test_set_strategy_sequential(self, test_config):
        """Test cambio a estrategia secuencial."""
        manager = PlaylistManager(test_config)
        
        manager.set_shuffle_mode(False)
        
        # Verificar que el modo shuffle está deshabilitado
        assert manager._playlist.shuffle_enabled is False
    
    def test_set_strategy_random(self, test_config):
        """Test cambio a estrategia shuffle."""
        manager = PlaylistManager(test_config)
        
        manager.set_shuffle_mode(True)
        
        # Verificar que el modo shuffle está habilitado
        assert manager._playlist.shuffle_enabled is True
    
    def test_set_strategy_shuffle(self, test_config):
        """Test cambio a estrategia shuffle."""
        manager = PlaylistManager(test_config)
        
        manager.set_shuffle_mode(True)
        
        # Verificar que el modo shuffle está habilitado
        assert manager._playlist.shuffle_enabled is True
    
    def test_set_strategy_invalid(self, test_config):
        """Test cambio entre modos shuffle y secuencial."""
        manager = PlaylistManager(test_config)
        original_shuffle_mode = manager._playlist.shuffle_enabled
        
        # Cambiar a shuffle
        manager.set_shuffle_mode(True)
        assert manager._playlist.shuffle_enabled is True
        
        # Cambiar a secuencial
        manager.set_shuffle_mode(False)
        assert manager._playlist.shuffle_enabled is False
    
    def test_load_videos_from_directory_success(self, test_config, sample_video_files):
        """Test carga exitosa de videos desde directorio."""
        manager = PlaylistManager(test_config)
        
        result = manager.load_videos_from_directory()
        
        assert result == len(sample_video_files)
        assert len(manager._playlist.videos) == len(sample_video_files)
    
    def test_load_videos_from_directory_no_videos(self, test_config):
        """Test carga cuando no hay videos."""
        manager = PlaylistManager(test_config)
        
        # Usar un directorio vacío
        empty_dir = test_config.video_dir / "empty"
        empty_dir.mkdir(exist_ok=True)
        
        result = manager.load_videos_from_directory(str(empty_dir))
        
        assert result == 0
        assert len(manager._playlist.videos) == 0
    
    def test_load_videos_from_directory_exception(self, test_config):
        """Test carga con directorio inexistente."""
        manager = PlaylistManager(test_config)
        
        result = manager.load_videos_from_directory("/nonexistent/directory")
        
        assert result == 0
        assert len(manager._playlist.videos) == 0
    
    def test_get_current_video_empty_playlist(self, test_config):
        """Test obtener video actual con playlist vacía."""
        manager = PlaylistManager(test_config)
        
        result = manager.get_current_video()
        
        assert result is None
    
    def test_get_current_video_with_videos(self, test_config, sample_video_info):
        """Test obtener video actual con videos."""
        manager = PlaylistManager(test_config)
        manager._playlist.videos = sample_video_info
        manager._playlist.current_index = 1
        
        result = manager.get_current_video()
        
        assert result == sample_video_info[1]
    
    def test_get_next_video_delegates_to_strategy(self, test_config, sample_video_info):
        """Test que get_next_video delega a la estrategia."""
        manager = PlaylistManager(test_config)
        manager._playlist.videos = sample_video_info
        
        # Mock de la estrategia
        mock_strategy = Mock()
        mock_strategy.get_next_video.return_value = sample_video_info[1]
        manager._current_strategy = mock_strategy  # Usar el atributo correcto
        
        result = manager.get_next_video()
        
        assert result == sample_video_info[1]
        mock_strategy.get_next_video.assert_called_once_with(manager._playlist)
    
    def test_is_empty_true(self, test_config):
        """Test is_empty con playlist vacía."""
        manager = PlaylistManager(test_config)
        
        assert manager.is_empty() is True
    
    def test_is_empty_false(self, test_config, sample_video_info):
        """Test is_empty con videos."""
        manager = PlaylistManager(test_config)
        manager._playlist.videos = sample_video_info
        
        assert manager.is_empty() is False
    
    def test_get_video_count(self, test_config, sample_video_info):
        """Test obtener número de videos."""
        manager = PlaylistManager(test_config)
        manager._playlist.videos = sample_video_info
        
        result = manager.get_video_count()
        
        assert result == len(sample_video_info)
    
    def test_reset_playlist(self, test_config, sample_video_info):
        """Test reset de playlist."""
        manager = PlaylistManager(test_config)
        manager._playlist.videos = sample_video_info
        manager._playlist.current_index = 2
        
        manager.reset_playlist()
        
        # El reset debería haber puesto el índice en 0
        assert manager._playlist.current_index == 0
    
    def test_get_playlist_info(self, test_config, sample_video_info):
        """Test obtener información de playlist."""
        manager = PlaylistManager(test_config)
        manager._playlist.videos = sample_video_info
        manager._playlist.current_index = 1
        manager._playlist.loop_enabled = True
        manager._playlist.shuffle_enabled = False
        
        result = manager.get_playlist_info()
        
        expected = {
            'total_videos': len(sample_video_info),
            'current_index': 1,
            'current_video': sample_video_info[1].filename,
            'loop_enabled': True,
            'shuffle_enabled': False,
            'is_empty': False  # Usar el campo real que devuelve la implementación
        }
        
        assert result == expected
    
    def test_get_playlist_info_empty(self, test_config):
        """Test obtener información de playlist vacía."""
        manager = PlaylistManager(test_config)
        
        result = manager.get_playlist_info()
        
        expected = {
            'total_videos': 0,
            'current_index': 0,
            'current_video': None,
            'loop_enabled': True,
            'shuffle_enabled': False,
            'is_empty': True  # Usar el campo real que devuelve la implementación
        }
        
        assert result == expected