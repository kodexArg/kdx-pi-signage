"""Tests unitarios para SignageSystem."""

import pytest
import threading
import time
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from main import SignageSystem
from config import SystemConfig


class TestSignageSystem:
    """Tests para la clase SignageSystem."""
    
    def test_init_with_default_config(self):
        """Test inicialización con configuración por defecto."""
        system = SignageSystem()
        
        assert system.config is not None
        assert system.video_player is None
        assert system.playlist_manager is None
        assert system.video_scanner is None
        assert system._running is False
        assert system._error_count == 0
        assert system._consecutive_errors == 0
    
    def test_init_with_custom_config(self, test_config):
        """Test inicialización con configuración personalizada."""
        system = SignageSystem(test_config)
        
        assert system.config == test_config
        assert system.config.video_dir == test_config.video_dir
    
    @patch('main.VideoScanner')
    @patch('main.PlaylistManager')
    @patch('main.VideoPlayer')
    def test_initialize_success(self, mock_video_player, mock_playlist_manager, 
                               mock_video_scanner, test_config):
        """Test inicialización exitosa de componentes."""
        # Setup mocks
        mock_scanner_instance = Mock()
        mock_scanner_instance.validate_directory.return_value = True
        mock_video_scanner.return_value = mock_scanner_instance
        
        mock_manager_instance = Mock()
        mock_manager_instance.load_videos_from_directory.return_value = 3
        mock_playlist_manager.return_value = mock_manager_instance
        
        mock_player_instance = Mock()
        mock_video_player.return_value = mock_player_instance
        
        system = SignageSystem(test_config)
        result = system.initialize()
        
        assert result is True
        assert system.video_scanner is not None
        assert system.playlist_manager is not None
        assert system.video_player is not None
        
        # Verificar que se configuraron los callbacks
        mock_player_instance.set_on_end_callback.assert_called_once()
        mock_player_instance.set_on_error_callback.assert_called_once()
        mock_scanner_instance.start_monitoring.assert_called_once()
    
    @patch('main.VideoScanner')
    def test_initialize_invalid_directory(self, mock_video_scanner, test_config):
        """Test inicialización con directorio inválido."""
        mock_scanner_instance = Mock()
        mock_scanner_instance.validate_directory.return_value = False
        mock_video_scanner.return_value = mock_scanner_instance
        
        system = SignageSystem(test_config)
        result = system.initialize()
        
        assert result is False
    
    @patch('main.VideoScanner')
    def test_initialize_exception(self, mock_video_scanner, test_config):
        """Test inicialización con excepción."""
        mock_video_scanner.side_effect = Exception("Test error")
        
        system = SignageSystem(test_config)
        result = system.initialize()
        
        assert result is False
    
    def test_start_already_running(self, test_config):
        """Test start cuando el sistema ya está ejecutándose."""
        system = SignageSystem(test_config)
        system._running = True
        
        result = system.start()
        
        assert result is True
    
    @patch('main.SignageSystem.initialize')
    def test_start_initialization_fails(self, mock_initialize, test_config):
        """Test start cuando la inicialización falla."""
        mock_initialize.return_value = False
        
        system = SignageSystem(test_config)
        result = system.start()
        
        assert result is False
        assert system._running is False
    
    @patch('main.SignageSystem.initialize')
    @patch('threading.Thread')
    def test_start_success(self, mock_thread, mock_initialize, test_config):
        """Test start exitoso."""
        mock_initialize.return_value = True
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance
        
        system = SignageSystem(test_config)
        result = system.start()
        
        assert result is True
        assert system._running is True
        mock_thread_instance.start.assert_called_once()
    
    def test_stop_not_running(self, test_config):
        """Test stop cuando el sistema no está ejecutándose."""
        system = SignageSystem(test_config)
        system._running = False
        
        # No debería hacer nada
        system.stop()
        
        assert system._running is False
    
    @patch('main.SignageSystem._cleanup')
    def test_stop_running(self, mock_cleanup, test_config):
        """Test stop cuando el sistema está ejecutándose."""
        system = SignageSystem(test_config)
        system._running = True
        
        # Mock del thread
        mock_thread = Mock()
        mock_thread.is_alive.return_value = False
        system._main_thread = mock_thread
        
        system.stop()
        
        assert system._running is False
        assert system._shutdown_event.is_set()
        mock_cleanup.assert_called_once()
    
    def test_wait_or_shutdown_timeout(self, test_config):
        """Test _wait_or_shutdown con timeout."""
        system = SignageSystem(test_config)
        
        start_time = time.time()
        result = system._wait_or_shutdown(0.1)
        end_time = time.time()
        
        assert result is True  # Completó la espera
        assert (end_time - start_time) >= 0.1
    
    def test_wait_or_shutdown_shutdown_signal(self, test_config):
        """Test _wait_or_shutdown con señal de parada."""
        system = SignageSystem(test_config)
        system._shutdown_event.set()
        
        start_time = time.time()
        result = system._wait_or_shutdown(1.0)
        end_time = time.time()
        
        assert result is False  # Se señaló parada
        assert (end_time - start_time) < 0.5  # Terminó antes del timeout
    
    def test_handle_playback_error(self, test_config):
        """Test manejo de errores de reproducción."""
        system = SignageSystem(test_config)
        initial_error_count = system._error_count
        initial_consecutive_errors = system._consecutive_errors
        
        system._handle_playback_error()
        
        assert system._error_count == initial_error_count + 1
        assert system._consecutive_errors == initial_consecutive_errors + 1
    
    @patch('main.SignageSystem._refresh_playlist')
    def test_handle_playback_error_max_retries(self, mock_refresh, test_config):
        """Test manejo de errores cuando se alcanzan los reintentos máximos."""
        system = SignageSystem(test_config)
        system._consecutive_errors = test_config.max_retries - 1
        
        system._handle_playback_error()
        
        mock_refresh.assert_called_once()
        assert system._consecutive_errors == 0
    
    def test_on_video_end_callback(self, test_config):
        """Test callback de fin de video."""
        system = SignageSystem(test_config)
        
        # No debería lanzar excepción
        system._on_video_end()
    
    @patch('main.SignageSystem._handle_playback_error')
    def test_on_video_error_callback(self, mock_handle_error, test_config):
        """Test callback de error de video."""
        system = SignageSystem(test_config)
        
        system._on_video_error()
        
        mock_handle_error.assert_called_once()
    
    @patch('threading.Thread')
    @patch('main.SignageSystem._refresh_playlist')
    def test_on_directory_change_callback(self, mock_refresh, mock_thread, test_config):
        """Test callback de cambio de directorio."""
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance
        
        system = SignageSystem(test_config)
        change_info = {'type': 'created', 'path': '/test/video.mp4'}
        
        system._on_directory_change(change_info)
        
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()
    
    def test_refresh_playlist_success(self, test_config, mock_playlist_manager):
        """Test actualización exitosa de playlist."""
        system = SignageSystem(test_config)
        system.playlist_manager = mock_playlist_manager
        mock_playlist_manager.load_videos_from_directory.return_value = 5
        
        system._refresh_playlist()
        
        mock_playlist_manager.load_videos_from_directory.assert_called_once()
    
    def test_refresh_playlist_exception(self, test_config, mock_playlist_manager):
        """Test actualización de playlist con excepción."""
        system = SignageSystem(test_config)
        system.playlist_manager = mock_playlist_manager
        mock_playlist_manager.load_videos_from_directory.side_effect = Exception("Test error")
        
        # No debería lanzar excepción
        system._refresh_playlist()
    
    def test_cleanup_success(self, test_config, mock_video_player, mock_video_scanner):
        """Test limpieza exitosa de recursos."""
        system = SignageSystem(test_config)
        system.video_player = mock_video_player
        system.video_scanner = mock_video_scanner
        
        system._cleanup()
        
        mock_video_player.cleanup.assert_called_once()
        mock_video_scanner.cleanup.assert_called_once()
    
    def test_cleanup_with_exception(self, test_config, mock_video_player):
        """Test limpieza con excepción."""
        system = SignageSystem(test_config)
        system.video_player = mock_video_player
        mock_video_player.cleanup.side_effect = Exception("Cleanup error")
        
        # No debería lanzar excepción
        system._cleanup()
    
    def test_get_system_status_minimal(self, test_config):
        """Test obtener estado del sistema sin componentes."""
        system = SignageSystem(test_config)
        
        status = system.get_system_status()
        
        assert 'running' in status
        assert 'error_count' in status
        assert 'consecutive_errors' in status
        assert 'current_video' in status
        assert 'playlist_info' in status
        assert 'directory_info' in status
        
        assert status['running'] is False
        assert status['error_count'] == 0
        assert status['consecutive_errors'] == 0
    
    def test_get_system_status_with_components(self, test_config, mock_video_player, 
                                             mock_playlist_manager, mock_video_scanner):
        """Test obtener estado del sistema con componentes."""
        system = SignageSystem(test_config)
        system.video_player = mock_video_player
        system.playlist_manager = mock_playlist_manager
        system.video_scanner = mock_video_scanner
        
        mock_video_player.get_current_video.return_value = "test_video.mp4"
        mock_video_player.is_playing.return_value = True
        mock_playlist_manager.get_playlist_info.return_value = {"count": 5}
        mock_video_scanner.get_directory_info.return_value = {"path": "/videos"}
        
        status = system.get_system_status()
        
        assert status['current_video'] == "test_video.mp4"
        assert status['is_playing'] is True
        assert status['playlist_info'] == {"count": 5}
        assert status['directory_info'] == {"path": "/videos"}