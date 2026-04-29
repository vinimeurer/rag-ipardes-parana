"""
Sistema de logging centralizado para o projeto RAG.
Garante que todos os módulos usem a mesma estratégia de logging.
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from .constants import LOGS_DIR, LOG_LEVEL, LOG_FORMAT


def setup_logger(name: str, log_file: str = None) -> logging.Logger:
    """
    Configura um logger para um módulo específico.
    
    Args:
        name: Nome do logger (geralmente __name__ do módulo)
        log_file: Caminho opcional para arquivo de log
        
    Returns:
        Logger configurado
        
    Example:
        ```python
        from src.core.logger import setup_logger
        logger = setup_logger(__name__)
        logger.info("Iniciando extração de PDFs...")
        ```
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # Handler para console (sempre)
    if not logger.handlers:  # Evitar duplicação
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, LOG_LEVEL))
        formatter = logging.Formatter(LOG_FORMAT)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Handler para arquivo (opcional)
        if log_file:
            LOGS_DIR.mkdir(parents=True, exist_ok=True)
            log_path = LOGS_DIR / log_file
            file_handler = logging.FileHandler(log_path, encoding="utf-8")
            file_handler.setLevel(getattr(logging, LOG_LEVEL))
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    
    return logger


def get_timestamped_logfile(prefix: str) -> str:
    """
    Gera nome de arquivo de log com timestamp.
    
    Args:
        prefix: Prefixo do arquivo (ex: "ingest", "api")
        
    Returns:
        Nome do arquivo de log
        
    Example:
        >>> get_timestamped_logfile("ingest")
        'ingest_20260429_103045.log'
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.log"
