"""Tests unitarios para VideoScanner."""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from video_scanner import VideoScanner, VideoFileHandler


class TestVideoFileHandler:
    """Tests para VideoFileHandler."""
    
    def test_init(self):
        """Test inicialización del handler."""
        supported_formats = ['.mp4', '.avi', '.MKV']
        callback = Mock()
        
        handler = VideoFileHandler(supported_formats, callback)
        
        assert handler.supported_formats == ['.mp4', '.avi', '.mkv']  # Convertidos a minúsculas
        assert handler.callback == callback
    
    def test_is_video_file_true(self):
        """Test identificación de archivo de video válido."""
        handler = VideoFileHandler(['.mp4', '.avi'])
        
        assert handler._is_video_file('/path/to/video.mp4') is True
        assert handler._is_video_file('/path/to/video.AVI') is True  # Case insensitive
    
    def test_is_video_file_false(self):
        """Test identificación de archivo no-video."""
        handler = VideoFileHandler(['.mp4', '.avi'])
        
        assert handler._is_video_file('/path/to/document.txt') is False
        assert handler._is_video_file('/path/to/image.jpg') is False
    
    def test_on_created_video_file(self):
        """Test evento de creación de archivo de video."""
        callback = Mock()
        handler = VideoFileHandler(['.mp4'], callback)
        
        # Mock del evento
        event = Mock()
        event.is_directory = False
        event.src_path = '/path/to/new_video.mp4'
        
        handler.on_created(event)
        
        callback.assert_called_once_with('created', '/path/to/new_video.mp4')
    
    def test_on_created_non_video_file(self):
        """Test evento de creación de archivo no-video."""
        callback = Mock()
        handler = VideoFileHandler(['.mp4'], callback)
        
        event = Mock()
        event.is_directory = False
        event.src_path = '/path/to/document.txt'
        
        handler.on_created(event)
        
        callback.assert_not_called()
    
    def test_on_created_directory(self):
        """Test evento de creación de directorio."""
        callback = Mock()
        handler = VideoFileHandler(['.mp4'], callback)
        
        event = Mock()
        event.is_directory = True
        event.src_path = '/path/to/directory'
        
        handler.on_created(event)
        
        callback.assert_not_called()
    
    def test_on_deleted_video_file(self):
        """Test evento de eliminación de archivo de video."""
        callback = Mock()
        handler = VideoFileHandler(['.mp4'], callback)
        
        event = Mock()
        event.is_directory = False
        event.src_path = '/path/to/deleted_video.mp4'
        
        handler.on_deleted(event)
        
        callback.assert_called_once_with('deleted', '/path/to/deleted_video.mp4')
    
    def test_on_moved_video_to_video(self):
        """Test evento de movimiento de video a video."""
        callback = Mock()
        handler = VideoFileHandler(['.mp4'], callback)
        
        event = Mock()
        event.is_directory = False
        event.src_path = '/path/old_video.mp4'
        event.dest_path = '/path/new_video.mp4'
        
        handler.on_moved(event)
        
        # Debería llamar callback dos veces: deleted y created
        assert callback.call_count == 2
        callback.assert_any_call('deleted', '/path/old_video.mp4')
        callback.assert_any_call('created', '/path/new_video.mp4')
    
    def test_on_moved_non_video_to_video(self):
        """Test evento de movimiento de no-video a video."""
        callback = Mock()
        handler = VideoFileHandler(['.mp4'], callback)
        
        event = Mock()
        event.is_directory = False
        event.src_path = '/path/document.txt'
        event.dest_path = '/path/new_video.mp4'
        
        handler.on_moved(event)
        
        callback.assert_called_once_with('created', '/path/new_video.mp4')
    
    def test_on_moved_video_to_non_video(self):
        """Test evento de movimiento de video a no-video."""
        callback = Mock()
        handler = VideoFileHandler(['.mp4'], callback)
        
        event = Mock()
        event.is_directory = False
        event.src_path = '/path/old_video.mp4'
        event.dest_path = '/path/document.txt'
        
        handler.on_moved(event)
        
        callback.assert_called_once_with('deleted', '/path/old_video.mp4')


class TestVideoScanner:
    """Tests para VideoScanner."""
    
    def test_init(self, test_config):
        """Test inicialización del scanner."""
        scanner = VideoScanner(test_config)
        
        assert scanner.config == test_config
        assert scanner._observer is None
        assert scanner._is_monitoring is False
        assert scanner._cached_videos == set()
        assert scanner._last_scan_time is None
    
    def test_validate_directory_exists_and_accessible(self, test_config, video_dir):
        """Test validación de directorio existente y accesible."""
        scanner = VideoScanner(test_config)
        
        result = scanner.validate_directory()
        
        assert result is True
    
    def test_validate_directory_not_exists(self, test_config):
        """Test validación de directorio inexistente."""
        # Cambiar a directorio que no existe
        test_config.video_dir = Path('/nonexistent/directory')
        scanner = VideoScanner(test_config)
        
        result = scanner.validate_directory()
        
        assert result is False
    
    def test_validate_directory_not_a_directory(self, test_config, temp_dir):
        """Test validación cuando la ruta no es un directorio."""
        # Crear un archivo en lugar de directorio
        file_path = temp_dir / "not_a_directory.txt"
        file_path.write_text("test")
        test_config.video_dir = file_path
        
        scanner = VideoScanner(test_config)
        
        result = scanner.validate_directory()
        
        assert result is False
    
    def test_scan_videos_success(self, test_config, sample_video_files):
        """Test escaneo exitoso de videos."""
        scanner = VideoScanner(test_config)
        
        result = scanner.scan_videos()
        
        assert len(result) == len(sample_video_files)
        for video_file in sample_video_files:
            assert str(video_file) in result
        
        # Verificar que se actualizó el caché
        assert len(scanner._cached_videos) == len(sample_video_files)
        assert scanner._last_scan_time is not None
    
    def test_scan_videos_custom_directory(self, test_config, temp_dir):
        """Test escaneo de directorio personalizado."""
        # Crear directorio personalizado con videos
        custom_dir = temp_dir / "custom_videos"
        custom_dir.mkdir()
        
        video_file = custom_dir / "custom_video.mp4"
        video_file.write_text("fake video")
        
        scanner = VideoScanner(test_config)
        
        result = scanner.scan_videos(str(custom_dir))
        
        assert len(result) == 1
        assert str(video_file) in result
    
    def test_scan_videos_no_videos(self, test_config):
        """Test escaneo sin videos."""
        scanner = VideoScanner(test_config)
        
        result = scanner.scan_videos()
        
        assert result == []
        assert len(scanner._cached_videos) == 0
    
    def test_scan_videos_exception(self, test_config):
        """Test escaneo con excepción."""
        # Directorio que causará excepción
        test_config.video_dir = Path('/nonexistent')
        scanner = VideoScanner(test_config)
        
        result = scanner.scan_videos()
        
        assert result == []
    
    def test_refresh_playlist(self, test_config, sample_video_files):
        """Test actualización de playlist."""
        scanner = VideoScanner(test_config)
        
        result = scanner.refresh_playlist()
        
        assert len(result) == len(sample_video_files)
    
    @patch('video_scanner.Observer')
    def test_start_monitoring_success(self, mock_observer_class, test_config):
        """Test inicio exitoso de monitoreo."""
        mock_observer = Mock()
        mock_observer_class.return_value = mock_observer
        
        scanner = VideoScanner(test_config)
        callback = Mock()
        
        result = scanner.start_monitoring(callback)
        
        assert result is True
        assert scanner._is_monitoring is True
        assert scanner._observer == mock_observer
        
        mock_observer.schedule.assert_called_once()
        mock_observer.start.assert_called_once()
    
    @patch('video_scanner.Observer')
    def test_start_monitoring_already_monitoring(self, mock_observer_class, test_config):
        """Test inicio de monitoreo cuando ya está monitoreando."""
        scanner = VideoScanner(test_config)
        scanner._is_monitoring = True
        
        result = scanner.start_monitoring()
        
        assert result is True
        mock_observer_class.assert_not_called()
    
    @patch('video_scanner.Observer')
    def test_start_monitoring_exception(self, mock_observer_class, test_config):
        """Test inicio de monitoreo con excepción."""
        mock_observer_class.side_effect = Exception("Observer error")
        
        scanner = VideoScanner(test_config)
        
        result = scanner.start_monitoring()
        
        assert result is False
        assert scanner._is_monitoring is False
    
    def test_stop_monitoring_not_monitoring(self, test_config):
        """Test parada de monitoreo cuando no está monitoreando."""
        scanner = VideoScanner(test_config)
        
        result = scanner.stop_monitoring()
        
        assert result is True
    
    def test_stop_monitoring_success(self, test_config):
        """Test parada exitosa de monitoreo."""
        scanner = VideoScanner(test_config)
        scanner._is_monitoring = True
        
        mock_observer = Mock()
        scanner._observer = mock_observer
        
        result = scanner.stop_monitoring()
        
        assert result is True
        assert scanner._is_monitoring is False
        assert scanner._observer is None
        
        mock_observer.stop.assert_called_once()
        mock_observer.join.assert_called_once_with(timeout=5)
    
    def test_stop_monitoring_exception(self, test_config):
        """Test parada de monitoreo con excepción."""
        scanner = VideoScanner(test_config)
        scanner._is_monitoring = True
        
        mock_observer = Mock()
        mock_observer.stop.side_effect = Exception("Stop error")
        scanner._observer = mock_observer
        
        result = scanner.stop_monitoring()
        
        assert result is False
        assert scanner._is_monitoring is True  # No cambió por la excepción
    
    def test_handle_file_change_created(self, test_config):
        """Test manejo de cambio de archivo - creado."""
        callback = Mock()
        scanner = VideoScanner(test_config)
        
        scanner._handle_file_change('created', '/path/to/new_video.mp4')
        
        # Debería actualizar el caché interno
        # (implementación específica depende del código real)
    
    def test_handle_file_change_deleted(self, test_config):
        """Test manejo de cambio de archivo - eliminado."""
        scanner = VideoScanner(test_config)
        scanner._cached_videos.add('/path/to/video.mp4')
        
        scanner._handle_file_change('deleted', '/path/to/video.mp4')
        
        # El video debería ser removido del caché
        assert '/path/to/video.mp4' not in scanner._cached_videos
    
    def test_handle_file_change_exception(self, test_config):
        """Test manejo de cambio con excepción."""
        scanner = VideoScanner(test_config)
        
        # No debería lanzar excepción
        scanner._handle_file_change('invalid_event', '/path/to/video.mp4')
    
    def test_is_monitoring_true(self, test_config):
        """Test verificación de estado de monitoreo - activo."""
        scanner = VideoScanner(test_config)
        scanner._is_monitoring = True
        
        assert scanner.is_monitoring() is True
    
    def test_is_monitoring_false(self, test_config):
        """Test verificación de estado de monitoreo - inactivo."""
        scanner = VideoScanner(test_config)
        
        assert scanner.is_monitoring() is False
    
    def test_get_last_scan_time_none(self, test_config):
        """Test obtener tiempo de último escaneo - nunca escaneado."""
        scanner = VideoScanner(test_config)
        
        assert scanner.get_last_scan_time() is None
    
    def test_get_last_scan_time_with_scan(self, test_config, sample_video_files):
        """Test obtener tiempo de último escaneo después de escanear."""
        scanner = VideoScanner(test_config)
        
        before_scan = time.time()
        scanner.scan_videos()
        after_scan = time.time()
        
        last_scan_time = scanner.get_last_scan_time()
        
        assert last_scan_time is not None
        assert before_scan <= last_scan_time <= after_scan
    
    def test_get_directory_info(self, test_config, sample_video_files):
        """Test obtener información del directorio."""
        scanner = VideoScanner(test_config)
        scanner.scan_videos()  # Para poblar el caché
        
        result = scanner.get_directory_info()
        
        assert 'path' in result
        assert 'video_count' in result
        assert 'last_scan_time' in result
        assert 'is_monitoring' in result
        
        assert result['path'] == str(test_config.video_dir)
        assert result['video_count'] == len(sample_video_files)
        assert result['is_monitoring'] is False
    
    def test_cleanup_not_monitoring(self, test_config):
        """Test limpieza cuando no está monitoreando."""
        scanner = VideoScanner(test_config)
        
        # No debería lanzar excepción
        scanner.cleanup()
    
    def test_cleanup_monitoring(self, test_config):
        """Test limpieza cuando está monitoreando."""
        scanner = VideoScanner(test_config)
        scanner._is_monitoring = True
        
        mock_observer = Mock()
        scanner._observer = mock_observer
        
        scanner.cleanup()
        
        mock_observer.stop.assert_called_once()
        mock_observer.join.assert_called_once_with(timeout=5)
        assert scanner._is_monitoring is False
        assert scanner._observer is None