import os
import sys
from loguru import logger
from app.core.config import settings


def setup_logging():
    """Configura o sistema de logging da aplicação"""
    
    # Remove o handler padrão do loguru
    logger.remove()
    
    # Cria o diretório de logs se não existir
    log_dir = os.path.dirname(settings.log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Formato personalizado
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # Handler para console
    logger.add(
        sys.stdout,
        format=log_format,
        level=settings.log_level,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # Handler para arquivo
    logger.add(
        settings.log_file,
        format=log_format,
        level=settings.log_level,
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        backtrace=True,
        diagnose=True
    )
    
    logger.info("Sistema de logging configurado")


def get_logger(name: str = None):
    """Retorna uma instância do logger"""
    if name:
        return logger.bind(name=name)
    return logger
