import logging
import logging.handlers
import os
from pathlib import Path

script_dir = Path(__file__).parent.parent 
logs_dir = script_dir / 'logs'

logs_dir.mkdir(exist_ok=True)

def setup_logger():
    """Configurar el sistema de logging"""
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(name)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        if isinstance(handler, logging.StreamHandler):
            root_logger.removeHandler(handler)

    root_logger.setLevel(logging.WARNING)
    
    logger = logging.getLogger('Posada')
    logger.setLevel(logging.DEBUG)
    
    logger.handlers.clear()
    
    file_handler = logging.handlers.RotatingFileHandler(
        filename=logs_dir / 'app.log',
        maxBytes=10 * 1024 * 1024,  # 10MB máximo
        backupCount=5,              # 5 archivos de respaldo
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(
            '%(asctime)s - %(levelname)s - %(name)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    )
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR) 
    console_handler.setFormatter(
        logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
    )
    
    error_handler = logging.FileHandler(
        filename=logs_dir / 'errors.log',
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(
        logging.Formatter(
            '%(asctime)s - %(levelname)s - %(name)s - %(funcName)s:%(lineno)d - %(message)s\n'
            'Exception: %(exc_info)s\n' + '-'*50,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    )
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.addHandler(error_handler)
    
    return logger

logger = setup_logger()

# Funciones útiles adicionales

def log_startup():
    """Log cuando la aplicación inicia"""
    logger.info("=" * 50)
    logger.info("🚀 POSADA - Sistema iniciado")
    logger.info("=" * 50)

def log_shutdown():
    """Log cuando la aplicación termina"""
    logger.info("=" * 50)
    logger.info("🛑 POSADA - Sistema detenido")
    logger.info("=" * 50)

def log_database_connection(success: bool, details: str = ""):
    """Log específico para conexiones de base de datos"""
    if success:
        logger.info(f"✅ Conexión a base de datos exitosa {details}")
    else:
        logger.error(f"❌ Error en conexión a base de datos {details}")

def log_api_request(method: str, endpoint: str, status_code: int = None):
    """Log para requests de API"""
    if status_code:
        logger.info(f"🌐 {method} {endpoint} - Status: {status_code}")
    else:
        logger.info(f"🌐 {method} {endpoint}")