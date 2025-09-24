"""Tests unitarios para modelos de configuración."""

import pytest
from pathlib import Path
from pydantic import ValidationError

from config import SystemConfig, VLCConfig, VideoInfo, Playlist, PlayerState


class TestSystemConfig:
    """Tests para SystemConfig."""
    
    def test_default_values(self):
        """Test valores por defecto de SystemConfig."""
        config = SystemConfig()
        
        assert config.video_dir == Path('/home/pi/kdx-pi-signage/videos')
        assert config.log_dir == Path('/home/pi/kdx-pi-signage/logs')
        assert config.supported_formats == ['.mp4', '.avi', '.mkv', '.mov', '.wmv']
        assert config.refresh_interval == 30
        assert config.max_retries == 3
        assert config.retry_delay == 5
    
    def test_custom_values(self, temp_dir):
        """Test valores personalizados de SystemConfig."""
        video_dir = temp_dir / "custom_videos"
        log_dir = temp_dir / "custom_logs"
        
        config = SystemConfig(
            video_dir=video_dir,
            log_dir=log_dir,
            supported_formats=['.mp4', '.avi'],
            refresh_interval=60,
            max_retries=5,
            retry_delay=10
        )
        
        assert config.video_dir == video_dir
        assert config.log_dir == log_dir
        assert config.supported_formats == ['.mp4', '.avi']
        assert config.refresh_interval == 60
        assert config.max_retries == 5
        assert config.retry_delay == 10
    
    def test_validate_directories_creates_missing(self, temp_dir):
        """Test que los validadores crean directorios faltantes."""
        video_dir = temp_dir / "new_videos"
        log_dir = temp_dir / "new_logs"
        
        # Los directorios no existen inicialmente
        assert not video_dir.exists()
        assert not log_dir.exists()
        
        config = SystemConfig(video_dir=video_dir, log_dir=log_dir)
        
        # Los directorios deberían haberse creado
        assert config.video_dir.exists()
        assert config.log_dir.exists()
    
    def test_validate_directories_string_input(self, temp_dir):
        """Test validación de directorios con entrada string."""
        video_dir_str = str(temp_dir / "string_videos")
        
        config = SystemConfig(video_dir=video_dir_str)
        
        assert isinstance(config.video_dir, Path)
        assert config.video_dir.exists()
    
    def test_validate_formats_valid(self):
        """Test validación de formatos válidos."""
        config = SystemConfig(supported_formats=['.mp4', '.avi', '.mkv'])
        
        assert config.supported_formats == ['.mp4', '.avi', '.mkv']
    
    def test_validate_formats_invalid(self):
        """Test validación de formatos inválidos."""
        with pytest.raises(ValidationError, match="Formato debe comenzar con punto"):
            SystemConfig(supported_formats=['mp4', '.avi'])
    
    def test_refresh_interval_validation(self):
        """Test validación de intervalo de refresco."""
        # Valor válido
        config = SystemConfig(refresh_interval=60)
        assert config.refresh_interval == 60
        
        # Valor muy bajo
        with pytest.raises(ValidationError):
            SystemConfig(refresh_interval=1)
        
        # Valor muy alto
        with pytest.raises(ValidationError):
            SystemConfig(refresh_interval=500)
    
    def test_max_retries_validation(self):
        """Test validación de reintentos máximos."""
        # Valor válido
        config = SystemConfig(max_retries=5)
        assert config.max_retries == 5
        
        # Valor muy bajo
        with pytest.raises(ValidationError):
            SystemConfig(max_retries=0)
        
        # Valor muy alto
        with pytest.raises(ValidationError):
            SystemConfig(max_retries=15)
    
    def test_retry_delay_validation(self):
        """Test validación de delay de reintentos."""
        # Valor válido
        config = SystemConfig(retry_delay=10)
        assert config.retry_delay == 10
        
        # Valor muy bajo
        with pytest.raises(ValidationError):
            SystemConfig(retry_delay=0)
        
        # Valor muy alto
        with pytest.raises(ValidationError):
            SystemConfig(retry_delay=100)


class TestVLCConfig:
    """Tests para VLCConfig."""
    
    def test_default_values(self):
        """Test valores por defecto de VLCConfig."""
        config = VLCConfig()
        
        assert config.interface == 'dummy'
        assert config.fullscreen is True
        assert config.show_video_title is False
        assert config.show_osd is False
        assert config.enable_subtitles is False
        assert config.enable_audio is False
        assert config.quiet_mode is True
        assert config.video_output == 'mmal_vout'
        assert config.codec == 'mmal'
    
    def test_custom_values(self):
        """Test valores personalizados de VLCConfig."""
        config = VLCConfig(
            interface='qt',
            fullscreen=False,
            show_video_title=True,
            enable_audio=True,
            quiet_mode=False
        )
        
        assert config.interface == 'qt'
        assert config.fullscreen is False
        assert config.show_video_title is True
        assert config.enable_audio is True
        assert config.quiet_mode is False
    
    def test_to_vlc_args_default(self):
        """Test conversión a argumentos VLC con configuración por defecto."""
        config = VLCConfig()
        
        args = config.to_vlc_args()
        
        expected_args = [
            '--intf', 'dummy',
            '--no-video-title-show',
            '--fullscreen',
            '--no-osd',
            '--no-spu',
            '--no-audio',
            '--quiet',
            '--vout', 'mmal_vout',
            '--codec', 'mmal'
        ]
        
        assert args == expected_args
    
    def test_to_vlc_args_custom(self):
        """Test conversión a argumentos VLC con configuración personalizada."""
        config = VLCConfig(
            interface='qt',
            fullscreen=False,
            show_video_title=True,
            show_osd=True,
            enable_subtitles=True,
            enable_audio=True,
            quiet_mode=False
        )
        
        args = config.to_vlc_args()
        
        expected_args = [
            '--intf', 'qt',
            '--vout', 'mmal_vout',
            '--codec', 'mmal'
        ]
        
        assert args == expected_args


class TestVideoInfo:
    """Tests para VideoInfo."""
    
    def test_valid_video_info(self, sample_video_files):
        """Test creación de VideoInfo válido."""
        video_file = sample_video_files[0]
        
        video_info = VideoInfo(
            file_path=video_file,
            filename=video_file.name,
            file_size=video_file.stat().st_size,
            format_extension=video_file.suffix,
            is_valid=True,
            last_modified=video_file.stat().st_mtime
        )
        
        assert video_info.file_path == video_file
        assert video_info.filename == video_file.name
        assert video_info.file_size > 0
        assert video_info.format_extension == video_file.suffix
        assert video_info.is_valid is True
    
    def test_validate_file_exists(self, sample_video_files):
        """Test validación de archivo existente."""
        video_file = sample_video_files[0]
        
        # Debería funcionar sin problemas
        video_info = VideoInfo(
            file_path=video_file,
            filename=video_file.name,
            file_size=100,
            format_extension='.mp4'
        )
        
        assert video_info.file_path == video_file
    
    def test_validate_file_not_exists(self):
        """Test validación de archivo inexistente."""
        with pytest.raises(ValidationError, match="Archivo no encontrado"):
            VideoInfo(
                file_path=Path('/nonexistent/video.mp4'),
                filename='video.mp4',
                file_size=100,
                format_extension='.mp4'
            )
    
    def test_extract_filename_from_path(self, sample_video_files):
        """Test extracción automática de filename."""
        video_file = sample_video_files[0]
        
        video_info = VideoInfo(
            file_path=video_file,
            filename='',  # Será extraído automáticamente
            file_size=100,
            format_extension='.mp4'
        )
        
        assert video_info.filename == video_file.name
    
    def test_extract_extension_from_path(self, sample_video_files):
        """Test extracción automática de extensión."""
        video_file = sample_video_files[0]
        
        video_info = VideoInfo(
            file_path=video_file,
            filename=video_file.name,
            file_size=100,
            format_extension=''  # Será extraído automáticamente
        )
        
        assert video_info.format_extension == video_file.suffix.lower()
    
    def test_get_file_size_automatic(self, sample_video_files):
        """Test obtención automática de tamaño de archivo."""
        video_file = sample_video_files[0]
        
        video_info = VideoInfo(
            file_path=video_file,
            filename=video_file.name,
            file_size=0,  # Será calculado automáticamente
            format_extension='.mp4'
        )
        
        assert video_info.file_size == video_file.stat().st_size


class TestPlaylist:
    """Tests para Playlist."""
    
    def test_default_values(self):
        """Test valores por defecto de Playlist."""
        playlist = Playlist()
        
        assert playlist.videos == []
        assert playlist.current_index == 0
        assert playlist.shuffle_enabled is False
        assert playlist.loop_enabled is True
    
    def test_custom_values(self, sample_video_info):
        """Test valores personalizados de Playlist."""
        playlist = Playlist(
            videos=sample_video_info,
            current_index=1,
            shuffle_enabled=True,
            loop_enabled=False
        )
        
        assert playlist.videos == sample_video_info
        assert playlist.current_index == 1
        assert playlist.shuffle_enabled is True
        assert playlist.loop_enabled is False
    
    def test_validate_index_in_range(self, sample_video_info):
        """Test validación de índice dentro del rango."""
        playlist = Playlist(
            videos=sample_video_info,
            current_index=1
        )
        
        assert playlist.current_index == 1
    
    def test_validate_index_out_of_range(self, sample_video_info):
        """Test validación de índice fuera del rango."""
        playlist = Playlist(
            videos=sample_video_info,
            current_index=10  # Fuera del rango
        )
        
        # Debería resetear a 0
        assert playlist.current_index == 0
    
    def test_get_current_video_valid_index(self, sample_video_info):
        """Test obtener video actual con índice válido."""
        playlist = Playlist(
            videos=sample_video_info,
            current_index=1
        )
        
        result = playlist.get_current_video()
        
        assert result == sample_video_info[1]
    
    def test_get_current_video_empty_playlist(self):
        """Test obtener video actual con playlist vacía."""
        playlist = Playlist()
        
        result = playlist.get_current_video()
        
        assert result is None
    
    def test_get_current_video_invalid_index(self, sample_video_info):
        """Test obtener video actual con índice inválido."""
        playlist = Playlist(videos=sample_video_info)
        playlist.current_index = 10  # Forzar índice inválido
        
        result = playlist.get_current_video()
        
        assert result is None
    
    def test_get_next_video_with_loop(self, sample_video_info):
        """Test obtener siguiente video con bucle."""
        playlist = Playlist(
            videos=sample_video_info,
            current_index=len(sample_video_info) - 1,  # Último video
            loop_enabled=True
        )
        
        result = playlist.get_next_video()
        
        assert result == sample_video_info[0]  # Debería volver al primero
        assert playlist.current_index == 0
    
    def test_get_next_video_without_loop(self, sample_video_info):
        """Test obtener siguiente video sin bucle."""
        playlist = Playlist(
            videos=sample_video_info,
            current_index=len(sample_video_info) - 1,  # Último video
            loop_enabled=False
        )
        
        result = playlist.get_next_video()
        
        assert result is None
    
    def test_get_next_video_normal_sequence(self, sample_video_info):
        """Test obtener siguiente video en secuencia normal."""
        playlist = Playlist(
            videos=sample_video_info,
            current_index=0
        )
        
        result = playlist.get_next_video()
        
        assert result == sample_video_info[1]
        assert playlist.current_index == 1
    
    def test_reset_playlist(self, sample_video_info):
        """Test reset de playlist."""
        playlist = Playlist(
            videos=sample_video_info,
            current_index=2
        )
        
        playlist.reset_playlist()
        
        assert playlist.current_index == 0
    
    def test_is_empty_true(self):
        """Test is_empty con playlist vacía."""
        playlist = Playlist()
        
        assert playlist.is_empty() is True
    
    def test_is_empty_false(self, sample_video_info):
        """Test is_empty con videos."""
        playlist = Playlist(videos=sample_video_info)
        
        assert playlist.is_empty() is False


class TestPlayerState:
    """Tests para PlayerState."""
    
    def test_default_values(self):
        """Test valores por defecto de PlayerState."""
        state = PlayerState()
        
        assert state.current_video is None
        assert state.is_playing is False
        assert state.playlist_index == 0
        assert state.total_videos == 0
        assert state.playback_errors == 0
        assert state.last_scan_time is None
    
    def test_custom_values(self, sample_video_files):
        """Test valores personalizados de PlayerState."""
        # Usar un archivo de video real de las fixtures
        video_file = sample_video_files[0]
        
        state = PlayerState(
            current_video=str(video_file),
            is_playing=True,
            playlist_index=2,
            total_videos=5,
            playback_errors=1,
            last_scan_time=1234567890.0
        )
        
        assert state.current_video == str(video_file)
        assert state.is_playing is True
        assert state.playlist_index == 2
        assert state.total_videos == 5
        assert state.playback_errors == 1
        assert state.last_scan_time == 1234567890.0
    
    def test_validate_video_path_exists(self, sample_video_files):
        """Test validación de ruta de video existente."""
        video_file = sample_video_files[0]
        
        state = PlayerState(current_video=str(video_file))
        
        assert state.current_video == str(video_file)
    
    def test_validate_video_path_not_exists(self):
        """Test validación de ruta de video inexistente."""
        with pytest.raises(ValidationError, match="Archivo de video no encontrado"):
            PlayerState(current_video='/nonexistent/video.mp4')
    
    def test_validate_negative_values(self):
        """Test validación de valores negativos."""
        # playlist_index negativo
        with pytest.raises(ValidationError):
            PlayerState(playlist_index=-1)
        
        # total_videos negativo
        with pytest.raises(ValidationError):
            PlayerState(total_videos=-1)
        
        # playback_errors negativo
        with pytest.raises(ValidationError):
            PlayerState(playback_errors=-1)