# ==========================================
# config/database.py - Conexión PostgreSQL con configuración local
# ==========================================
import psycopg2
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from logging_config import *

def get_database_config():
    """
    Configuración local de la base de datos para desarrollo
    Modificar valores según la coonfiguración local
    """
    return {
        'host':'localhost',
        'database':'posada_db',
        'user':'postgres',
        'password':'joako2004@',
        'port':'5432'
    }

def verify_and_create_database(host, user, password, port, database_name):
    """
    Verificar si existe la base de datos y la crea si no existe
    """
    try:
        logger.info(f'Verificando la existencia de la base de datos: {database_name}')
        
        # Conectar a la base de datos por defecto posdtgres para verificar/crear
        connection_admin = psycopg2.connect(
            host=host,
            database='postgres',
            user=user,
            password=password,
            port=port
        )
        
        logger.debug('Conexión establecida con base de datos "postgres"')

        # Configurar para poder crear Bases de Datos
        connection_admin.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor_admin = connection_admin.cursor()
        
        # Verificar si la base de datos existe
        cursor_admin.execute(
            "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
            (database_name,)
        )
        exists = cursor_admin.fetchone()
        
        if not exists:
            # Crear la base de datos
            logger.warning(f'Base de datos "{database_name}" no existe. Creándola...')
            cursor_admin.execute(f'CREATE DATABASE "{database_name}"')
            logger.info(f'Base de datos "{database_name}" creada exitosamente')
            log_database_connection('CREATE DATABSE', database_name)
        else:
            logger.info(f'Base de datos "{database_name}" ya existe')
        
        # Cerrar la conexión administrativa
        cursor_admin.close()
        connection_admin.close()
        logger.debug('Conexión cerrada con éxito')
        
        return True
    
    except (Exception, Error) as e:
        logger.error(f'Error verificando/creando la base de datos:{e}', exc_info=True)

def connect_postgresql():
    """
    Establece la conexión con la base de datos PostgreSQL
    Verifica y crea la base de datos si no existe
    """
    # Obtener configuración local
    config = get_database_config()
    
    try:
        logger.info('Iniciando proceso de conexión a PostgreSQL')
        
        # Paso 1: verificar y crear base de datos si no existe
        log_database_connection('Verificando existencia de la base de datos...')
        if not verify_and_create_database(
            config['host'],
            config['user'],
            config['password'],
            config['port'],
            config['database']
        ):
            logger.error('No se puedo verificar/crear la base de datos')
            return None, None
        
        # Paso 2: Conectar a la base de datos específica
        log_database_connection(f'Conectando a la base de datos "{config['database']}"...')
        connection = psycopg2.connect(**config)
        
        # Crear cursor para ejecutar la consulta
        cursor = connection.cursor()
        
        # Verificar la conexión
        cursor.execute('SELECT version();')
        version = cursor.fetchone()
        logger.info('Conexión exitosa a PostgreSQL')
        log_database_connection(f'Versión del servidor: {version[0]}')
        
        return connection, cursor
        
    except (Exception, Error) as e:
        logger.error(f'Error al conectar con PostgreSQL: {e}', exc_info=True)
        return None, None
    