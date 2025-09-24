"""Tests de integración para el sistema completo."""

import pytest
import time
import threading
from unittest.mock import Mock, patch
from pathlib import Path

from main import SignageSystem
from config import SystemConfig


class TestFullSystemIntegration:
    """Tests de integración para el sistema completo."""
    
    @patch('main.VideoPlayer')
    @patch('main.PlaylistManager')
    @patch('main.VideoScanner')
    def test_full_system_initialization(self, mock_scanner, mock_manager, mock_player, 
                                       test_config, sample_video_files):
        """Test inicialización completa del sistema."""
        # Setup mocks
        mock_scanner_instance = Mock()
        mock_scanner_instance.validate_directory.return_value = True
        mock_scanner.return_value = mock_scanner_instance
        
        mock_manager_instance = Mock()
        mock_manager_instance.load_videos_from_directory.return_value = len(sample_video_files)
        mock_manager_instance.is_empty.return_value = False
        mock_manager.return_value = mock_manager_instance
        
        mock_player_instance = Mock()
        mock_player.return_value = mock_player_instance
        
        # Test inicialización
        system = SignageSystem(test_config)
        result = system.initialize()
        
        assert result is True
        
        # Verificar que todos los componentes se inicializaron
        assert system.video_scanner is not None
        assert system.playlist_manager is not None
        assert system.video_player is not None
        
        # Verificar configuración de callbacks
        mock_player_instance.set_on_end_callback.assert_called_once()
        mock_player_instance.set_on_error_callback.assert_called_once()
        mock_scanner_instance.start_monitoring.assert_called_once()
    
    @patch('main.VideoPlayer')
    @patch('main.PlaylistManager')
    @patch('main.VideoScanner')
    def test_system_start_and_stop(self, mock_scanner, mock_manager, mock_player, test_config):
        """Test inicio y parada del sistema."""
        # Setup mocks
        mock_scanner_instance = Mock()
        mock_scanner_instance.validate_directory.return_value = True
        mock_scanner.return_value = mock_scanner_instance
        
        mock_manager_instance = Mock()
        mock_manager_instance.load_videos_from_directory.return_value = 3
        mock_manager.return_value = mock_manager_instance
        
        mock_player_instance = Mock()
        mock_player.return_value = mock_player_instance
        
        system = SignageSystem(test_config)
        
        # Test inicio
        result = system.start()
        assert result is True
        assert system._running is True
        assert system._main_thread is not None
        
        # Esperar un poco para que el thread se inicie
        time.sleep(0.1)
        
        # Test parada
        system.stop()
        assert system._running is False
        
        # Verificar limpieza
        mock_player_instance.cleanup.assert_called_once()
        mock_scanner_instance.cleanup.assert_called_once()
    
    @patch('main.VideoPlayer')
    @patch('main.PlaylistManager')
    @patch('main.VideoScanner')
    def test_video_playback_cycle(self, mock_scanner, mock_manager, mock_player, 
                                 test_config, sample_video_info):
        """Test ciclo completo de reproducción de videos."""
        # Setup mocks
        mock_scanner_instance = Mock()
        mock_scanner_instance.validate_directory.return_value = True
        mock_scanner.return_value = mock_scanner_instance
        
        mock_manager_instance = Mock()
        mock_manager_instance.load_videos_from_directory.return_value = len(sample_video_info)
        mock_manager_instance.is_empty.return_value = False
        mock_manager_instance.get_current_video.return_value = sample_video_info[0]
        mock_manager_instance.get_next_video.return_value = sample_video_info[1]
        mock_manager.return_value = mock_manager_instance
        
        mock_player_instance = Mock()
        mock_player_instance.play_video.return_value = True
        mock_player_instance.is_playing.side_effect = [True, True, False]  # Simular reproducción
        mock_player.return_value = mock_player_instance
        
        system = SignageSystem(test_config)
        system.initialize()
        
        # Simular un ciclo del bucle principal
        system._running = True
        
        # Ejecutar una iteración del bucle principal manualmente
        # (normalmente esto estaría en un thread separado)
        current_video = system.playlist_manager.get_current_video()
        assert current_video is not None
        
        play_result = system.video_player.play_video(str(current_video.file_path))
        assert play_result is True
        
        # Verificar que se llamaron los métodos correctos
        mock_manager_instance.get_current_video.assert_called()
        mock_player_instance.play_video.assert_called_once()
    
    @patch('main.VideoPlayer')
    @patch('main.PlaylistManager')
    @patch('main.VideoScanner')
    def test_error_handling_and_recovery(self, mock_scanner, mock_manager, mock_player, test_config):
        """Test manejo de errores y recuperación."""
        # Setup mocks
        mock_scanner_instance = Mock()
        mock_scanner_instance.validate_directory.return_value = True
        mock_scanner.return_value = mock_scanner_instance
        
        mock_manager_instance = Mock()
        mock_manager_instance.load_videos_from_directory.return_value = 1
        mock_manager_instance.is_empty.return_value = False
        mock_manager_instance.get_current_video.return_value = Mock(filename='test.mp4', file_path='/test.mp4')
        mock_manager.return_value = mock_manager_instance
        
        mock_player_instance = Mock()
        mock_player_instance.play_video.return_value = False  # Simular error
        mock_player.return_value = mock_player_instance
        
        system = SignageSystem(test_config)
        system.initialize()
        
        initial_error_count = system._error_count
        initial_consecutive_errors = system._consecutive_errors
        
        # Simular error de reproducción
        system._handle_playback_error()
        
        assert system._error_count == initial_error_count + 1
        assert system._consecutive_errors == initial_consecutive_errors + 1
    
    @patch('main.VideoPlayer')
    @patch('main.PlaylistManager')
    @patch('main.VideoScanner')
    def test_directory_change_handling(self, mock_scanner, mock_manager, mock_player, test_config):
        """Test manejo de cambios en el directorio."""
        # Setup mocks
        mock_scanner_instance = Mock()
        mock_scanner_instance.validate_directory.return_value = True
        mock_scanner.return_value = mock_scanner_instance
        
        mock_manager_instance = Mock()
        mock_manager_instance.load_videos_from_directory.return_value = 2
        mock_manager.return_value = mock_manager_instance
        
        mock_player_instance = Mock()
        mock_player.return_value = mock_player_instance
        
        system = SignageSystem(test_config)
        system.initialize()
        
        # Simular cambio en directorio
        change_info = {'type': 'created', 'path': '/new_video.mp4'}
        
        with patch('threading.Thread') as mock_thread:
            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance
            
            system._on_directory_change(change_info)
            
            # Verificar que se creó un thread para actualizar la playlist
            mock_thread.assert_called_once()
            mock_thread_instance.start.assert_called_once()
    
    @patch('main.VideoPlayer')
    @patch('main.PlaylistManager')
    @patch('main.VideoScanner')
    def test_system_status_reporting(self, mock_scanner, mock_manager, mock_player, test_config):
        """Test reporte de estado del sistema."""
        # Setup mocks
        mock_scanner_instance = Mock()
        mock_scanner_instance.validate_directory.return_value = True
        mock_scanner_instance.get_directory_info.return_value = {'path': '/videos', 'count': 3}
        mock_scanner.return_value = mock_scanner_instance
        
        mock_manager_instance = Mock()
        mock_manager_instance.load_videos_from_directory.return_value = 3
        mock_manager_instance.get_playlist_info.return_value = {'total': 3, 'current': 1}
        mock_manager.return_value = mock_manager_instance
        
        mock_player_instance = Mock()
        mock_player_instance.get_current_video.return_value = 'current_video.mp4'
        mock_player_instance.is_playing.return_value = True
        mock_player.return_value = mock_player_instance
        
        system = SignageSystem(test_config)
        system.initialize()
        system._running = True
        system._error_count = 2
        system._consecutive_errors = 1
        
        status = system.get_system_status()
        
        # Verificar estructura del estado
        assert 'running' in status
        assert 'error_count' in status
        assert 'consecutive_errors' in status
        assert 'current_video' in status
        assert 'playlist_info' in status
        assert 'directory_info' in status
        assert 'is_playing' in status
        
        # Verificar valores
        assert status['running'] is True
        assert status['error_count'] == 2
        assert status['consecutive_errors'] == 1
        assert status['current_video'] == 'current_video.mp4'
        assert status['is_playing'] is True
        assert status['playlist_info'] == {'total': 3, 'current': 1}
        assert status['directory_info'] == {'path': '/videos', 'count': 3}
    
    @patch('main.VideoPlayer')
    @patch('main.PlaylistManager')
    @patch('main.VideoScanner')
    def test_max_retries_recovery(self, mock_scanner, mock_manager, mock_player, test_config):
        """Test recuperación después de alcanzar reintentos máximos."""
        # Setup mocks
        mock_scanner_instance = Mock()
        mock_scanner_instance.validate_directory.return_value = True
        mock_scanner.return_value = mock_scanner_instance
        
        mock_manager_instance = Mock()
        mock_manager_instance.load_videos_from_directory.return_value = 1
        mock_manager.return_value = mock_manager_instance
        
        mock_player_instance = Mock()
        mock_player.return_value = mock_player_instance
        
        system = SignageSystem(test_config)
        system.initialize()
        
        # Simular errores consecutivos hasta alcanzar el máximo
        system._consecutive_errors = test_config.max_retries - 1
        
        with patch.object(system, '_refresh_playlist') as mock_refresh:
            system._handle_playback_error()
            
            # Debería haber llamado a refresh_playlist
            mock_refresh.assert_called_once()
            # Y resetear los errores consecutivos
            assert system._consecutive_errors == 0
    
    def test_real_directory_operations(self, test_config, sample_video_files):
        """Test operaciones reales con directorio de archivos."""
        # Este test usa archivos reales (aunque simulados)
        from video_scanner import VideoScanner
        
        scanner = VideoScanner(test_config)
        
        # Test validación de directorio
        assert scanner.validate_directory() is True
        
        # Test escaneo de videos
        videos = scanner.scan_videos()
        assert len(videos) == len(sample_video_files)
        
        # Verificar que encontró los archivos correctos
        for video_file in sample_video_files:
            assert str(video_file) in videos
    
    def test_config_validation_integration(self, temp_dir):
        """Test integración de validación de configuración."""
        from config import SystemConfig, VLCConfig
        
        # Test creación de directorios automática
        video_dir = temp_dir / "auto_created_videos"
        log_dir = temp_dir / "auto_created_logs"
        
        config = SystemConfig(
            video_dir=video_dir,
            log_dir=log_dir,
            supported_formats=['.mp4', '.avi'],
            refresh_interval=10,
            max_retries=2,
            retry_delay=3
        )
        
        # Los directorios deberían haberse creado
        assert config.video_dir.exists()
        assert config.log_dir.exists()
        
        # Test configuración VLC
        vlc_config = VLCConfig(
            interface='dummy',
            fullscreen=True,
            enable_audio=False
        )
        
        args = vlc_config.to_vlc_args()
        assert '--intf' in args
        assert 'dummy' in args
        assert '--fullscreen' in args
        assert '--no-audio' in args