"""Sistema de logging unificado usando loguru (Singleton Pattern).

Este módulo implementa un sistema de logging centralizado para el sistema
de cartelería digital, utilizando el patrón Singleton para garantizar
una única instancia del logger en toda la aplicación.
"""

from loguru import logger
import sys
from pathlib import Path
from typing import Optional


class Logger:
    """Sistema de logging unificado usando loguru (Singleton Pattern).
    
    Esta clase implementa el patrón Singleton para proporcionar un sistema
    de logging centralizado y configurado para el sistema de cartelería digital.
    """
    
    _instance: Optional['Logger'] = None
    _configured: bool = False
    
    def __new__(cls) -> 'Logger':
        """Implementa el patrón Singleton para el logger."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def setup_logger(self, log_dir: str = "/home/pi/kdx-pi-signage/logs") -> None:
        """Configura el sistema de logging con loguru.
        
        Args:
            log_dir: Directorio donde se almacenarán los archivos de log
        """
        if self._configured:
            return
            
        # Crear directorio de logs si no existe
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        
        # Remover handler por defecto
        logger.remove()
        
        # Handler para consola (solo errores y warnings)
        logger.add(
            sys.stderr,
            level="WARNING",
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )
        
        # Handler para archivo principal con rotación
        logger.add(
            f"{log_dir}/signage.log",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="10 MB",
            retention="30 days",
            compression="zip"
        )
        
        # Handler para errores críticos
        logger.add(
            f"{log_dir}/errors.log",
            level="ERROR",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="1 day",
            retention="90 days"
        )
        
        self._configured = True
        logger.info("Sistema de logging configurado correctamente")
    
    def get_logger(self):
        """Obtiene la instancia del logger configurado.
        
        Returns:
            Logger configurado de loguru
        """
        if not self._configured:
            self.setup_logger()
        return logger


# Instancia global del logger
app_logger = Logger()