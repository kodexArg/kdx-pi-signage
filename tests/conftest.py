"""Configuración y fixtures compartidas para pytest."""

import pytest
import tempfile
import shutil
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from typing import Generator

# Mock VLC antes de cualquier importación
mock_vlc = MagicMock()
mock_vlc.Instance = MagicMock()
mock_vlc.MediaPlayer = MagicMock()
mock_vlc.EventType = MagicMock()
mock_vlc.EventType.MediaPlayerEndReached = 'EndReached'
mock_vlc.EventType.MediaPlayerEncounteredError = 'Error'
sys.modules['vlc'] = mock_vlc

from config import SystemConfig, VLCConfig, VideoInfo, Playlist
from logger import app_logger


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Crea un directorio temporal para tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def video_dir(temp_dir: Path) -> Path:
    """Crea un directorio temporal para videos de prueba."""
    video_path = temp_dir / "videos"
    video_path.mkdir(exist_ok=True)
    return video_path


@pytest.fixture
def log_dir(temp_dir: Path) -> Path:
    """Crea un directorio temporal para logs de prueba."""
    log_path = temp_dir / "logs"
    log_path.mkdir(exist_ok=True)
    return log_path


@pytest.fixture
def test_config(video_dir: Path, log_dir: Path) -> SystemConfig:
    """Configuración de prueba con directorios temporales."""
    return SystemConfig(
        video_dir=video_dir,
        log_dir=log_dir,
        supported_formats=['.mp4', '.avi', '.mkv'],
        refresh_interval=5,
        max_retries=2,
        retry_delay=1
    )


@pytest.fixture
def vlc_config() -> VLCConfig:
    """Configuración de VLC para pruebas."""
    return VLCConfig(
        interface='dummy',
        fullscreen=False,  # Para tests
        show_video_title=False,
        show_osd=False,
        enable_subtitles=False,
        enable_audio=False,
        quiet_mode=True
    )


@pytest.fixture
def sample_video_files(video_dir: Path) -> list[Path]:
    """Crea archivos de video de muestra para tests."""
    video_files = []
    
    # Crear archivos de video simulados
    for i, ext in enumerate(['.mp4', '.avi', '.mkv'], 1):
        video_file = video_dir / f"test_video_{i}{ext}"
        video_file.write_text(f"fake video content {i}")
        video_files.append(video_file)
    
    # Crear un archivo no-video para tests
    non_video = video_dir / "not_a_video.txt"
    non_video.write_text("this is not a video")
    
    return video_files


@pytest.fixture
def sample_video_info(sample_video_files: list[Path]) -> list[VideoInfo]:
    """Crea objetos VideoInfo de muestra."""
    video_infos = []
    for video_file in sample_video_files:
        video_info = VideoInfo(
            file_path=video_file,
            filename=video_file.name,
            file_size=video_file.stat().st_size,
            format_extension=video_file.suffix,
            is_valid=True,
            last_modified=video_file.stat().st_mtime
        )
        video_infos.append(video_info)
    return video_infos


@pytest.fixture
def sample_playlist(sample_video_info: list[VideoInfo]) -> Playlist:
    """Crea una playlist de muestra."""
    return Playlist(
        videos=sample_video_info,
        current_index=0,
        shuffle_enabled=False,
        loop_enabled=True
    )


@pytest.fixture
def mock_vlc_instance():
    """Mock de la instancia de VLC."""
    mock_instance = Mock()
    mock_player = Mock()
    mock_instance.media_player_new.return_value = mock_player
    return mock_instance, mock_player


@pytest.fixture
def mock_watchdog_observer():
    """Mock del Observer de watchdog."""
    mock_observer = Mock()
    mock_observer.start = Mock()
    mock_observer.stop = Mock()
    mock_observer.join = Mock()
    return mock_observer


@pytest.fixture(autouse=True)
def setup_logger():
    """Configura el logger para tests."""
    app_logger.setup_logger()
    yield
    # Cleanup si es necesario


@pytest.fixture
def mock_video_player():
    """Mock del VideoPlayer."""
    mock_player = Mock()
    mock_player.play_video.return_value = True
    mock_player.is_playing.return_value = False
    mock_player.cleanup = Mock()
    mock_player.set_on_end_callback = Mock()
    mock_player.set_on_error_callback = Mock()
    mock_player.get_current_video.return_value = None
    return mock_player


@pytest.fixture
def mock_playlist_manager():
    """Mock del PlaylistManager."""
    mock_manager = Mock()
    mock_manager.is_empty.return_value = False
    mock_manager.get_current_video.return_value = None
    mock_manager.get_next_video.return_value = None
    mock_manager.load_videos_from_directory.return_value = 0
    mock_manager.get_playlist_info.return_value = {}
    return mock_manager


@pytest.fixture
def mock_video_scanner():
    """Mock del VideoScanner."""
    mock_scanner = Mock()
    mock_scanner.validate_directory.return_value = True
    mock_scanner.start_monitoring.return_value = True
    mock_scanner.cleanup = Mock()
    mock_scanner.get_directory_info.return_value = {}
    return mock_scanner