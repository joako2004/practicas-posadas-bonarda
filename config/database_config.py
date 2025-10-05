# ==========================================
# config/database_config.py - Configuración de base de datos
# ==========================================
import os
import sys
from dotenv import load_dotenv
from .logging_config import logger

# Load environment variables
logger.info(f"Loading .env from current directory (CWD: {os.getcwd()})")
load_dotenv()
logger.info(f"DB_PASSWORD loaded: {bool(os.getenv('DB_PASSWORD'))}")
logger.info(f"All env vars with DB_: {[k for k in os.environ.keys() if k.startswith('DB_')]}")

def get_database_config():
    """
    Configuración de base de datos usando variables de entorno
    Valores por defecto para desarrollo local
    """
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'posada_db'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD'),
        'port': os.getenv('DB_PORT', '5432')
    }

def validate_database_config(config):
    """
    Valida que todas las configuraciones requeridas esten presentes
    """
    required_fields = ['host', 'database', 'user', 'password', 'port']
    missing_fields = []

    for field in required_fields:
        if not config.get(field):
            missing_fields.append(field.upper())

    if missing_fields:
        error_msg = f"❌ Variables de entorno faltantes: {', '.join(missing_fields)}"
        logger.error(error_msg)
        return False, error_msg

    # Validar que el puerto sea numérico
    try:
        int(config['port'])
    except ValueError:
        error_msg = "❌ DB_PORT debe ser un número válido"
        logger.error(error_msg)
        return False, error_msg

    logger.info("✅ Configuración de base de datos validada correctamente")
    return True, "Configuración válida"

def get_environment_info():
    """
    Información sobre el entorno actual
    """
    env_info = {
        'environment': os.getenv('ENVIRONMENT', 'development'),
        'db_host': os.getenv('DB_HOST', 'localhost'),
        'db_name': os.getenv('DB_NAME', 'posada_db'),
        'db_user': os.getenv('DB_USER', 'postgres'),
        'db_port': os.getenv('DB_PORT', '5432'),
        'password_configured': bool(os.getenv('DB_PASSWORD')),
        'python_version': sys.version,
        'working_directory': os.getcwd()
    }

    logger.info("🌍 Información del entorno:")
    for key, value in env_info.items():
        logger.info(f'  -{key}: {value}')

    return env_info

def test_environment_setup():
    """
    Prueba la configuración del entorno
    """
    logger.info("🧪 Probando configuración del entorno...")

    config = get_database_config()
    is_valid, message = validate_database_config(config)

    if is_valid:
        logger.info("✅ Configuración del entorno correcta")
        return True
    else:
        logger.error("❌ Problemas con la configuración del entorno")
        return False