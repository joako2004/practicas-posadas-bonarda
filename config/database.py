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
    Modifica estos valores según tu configuración local
    """
    return {
        'host': 'localhost',
        'database': 'posada_db',
        'user': 'postgres',
        'password': 'Joako2004@', 
        'port': '5432'
    }

def verify_and_create_database(host, user, password, port, database_name):
    """
    Verifica si existe la base de datos y la crea si no existe
    """
    try:
        logger.info(f"Verificando existencia de base de datos: {database_name}")
        
        # Conectar a la base de datos por defecto 'postgres' para verificar/crear
        admin_connection = psycopg2.connect(
            host=host,
            database="postgres",  # Base de datos por defecto de PostgreSQL
            user=user,
            password=password,
            port=port
        )
        
        logger.debug("Conexión administrativa establecida con base de datos 'postgres'")
        
        # Configurar para poder crear bases de datos
        admin_connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT) # se encarga de commitear las operaciones automáticamente
        admin_cursor = admin_connection.cursor()
        
        # Verificar si la base de datos existe
        admin_cursor.execute(
            "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", # para verificar la conexión, realiza una consulta al catálogo interno de postgresql
            (database_name,)
        )
        exists = admin_cursor.fetchone()
        
        if not exists:
            # Crear la base de datos
            logger.warning(f"Base de datos '{database_name}' no existe. Creándola...")
            admin_cursor.execute(f'CREATE DATABASE "{database_name}"')
            logger.info(f"Base de datos '{database_name}' creada exitosamente")
            log_database_connection(True, f"- Database '{database_name}' created")
        else:
            logger.info(f"Base de datos '{database_name}' ya existe")
            log_database_connection(True, f"- Database '{database_name}' already exists")
        
        # Cerrar conexión administrativa
        admin_cursor.close()
        admin_connection.close()
        logger.debug("Conexión administrativa cerrada")
        
        return True
        
    except (Exception, Error) as error:
        logger.error(f"Error verificando/creando base de datos: {error}", exc_info=True)
        log_database_connection(False, f"- Creation error: {error}")
        return False

def connect_postgresql():
    """
    Establece conexión con base de datos PostgreSQL
    Verifica y crea la base de datos si no existe
    """
    # Obtener configuración local
    config = get_database_config()
    
    try:
        logger.info("🔗 Iniciando proceso de conexión a PostgreSQL")
        
        # Paso 1: Verificar y crear base de datos si no existe
        logger.info("Verificando existencia de la base de datos...")
        if not verify_and_create_database(
            config['host'], 
            config['user'], 
            config['password'], 
            config['port'], 
            config['database']
        ):
            logger.error("No se pudo verificar/crear la base de datos")
            log_database_connection(False, "- Database verification failed")
            return None, None
        
        # Paso 2: Conectar a la base de datos específica
        logger.info(f"Conectando a la base de datos '{config['database']}'...")
        connection = psycopg2.connect(**config)
        
        # Crear cursor para ejecutar consultas
        cursor = connection.cursor()
        
        # Verificar la conexión
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        logger.info("✅ Conexión exitosa a PostgreSQL")
        logger.info(f"Versión del servidor: {version[0]}")
        
        log_database_connection(True, f"- Connected to '{config['database']}'")
        
        return connection, cursor
        
    except (Exception, Error) as error:
        logger.error(f"Error al conectar con PostgreSQL: {error}", exc_info=True)
        log_database_connection(False, f"- Connection error: {error}")
        return None, None

def verify_active_connection(connection):
    """
    Verifica si la conezión a la base de datos está activa
    """
    if connection is None:
        logger.warning('Conexión es None, considerada inactiva')
        return False
    
    try:
        # intentar ejecutar una consulta simple
        temp_cursor = connection.cursor()
        temp_cursor.execute('SELECT 1')
        temp_cursor.close()
        logger.debug('Verificación de conexión exitosa')
        return True
    except (Exception, Error) as error:
        logger.warning(f'Conexión inactiva detectada: {error}')
        return False

def reconnect_if_needed(connection, cursor):
    """
    Reconecta si la conexión se ha perdido
    """
    if not verify_active_connection(connection):
        logger.warning("🔄 Conexión perdida. Intentando reconectar...")
        
        # Cerrar recursos existentes
        if cursor:
            try:
                cursor.close()
                logger.debug('Cursor anterior cerrado')
            except:
                pass
        if connection:
            try:
                connection.close()
                logger.debug('Conexión anterior cerrada')
            except:
                pass
        
        # Reconectar
        new_connection, new_cursor = connect_postgresql()
        if new_connection and new_cursor:
            logger.info('✅ Reconexión exitosa')
            return new_connection, new_cursor
        else:
            logger.error("❌ No se pudo reconectar a la base de datos")
            return None, None
    
    logger.debug('Conexión activa, no es necesario reconectar')
    return connection, cursor

def execute_query(cursor, query, params=None):
    """
    Ejecuta una consulta SELECT y retorna los resultados
    """
    try:
        logger.debug(f'Ejecutando consulta: {query}')
        if params:
            cursor.execute(query, params)
            logger.debug(f'Parámetros de consulta: {params}')
        else:
            cursor.execute(query)
        
        results = cursor.fetchall()
        logger.info(f"✅ Consulta ejecutada exitosamente. Resultados: {len(results)} filas")
        return results
    
    except Error as error:
        logger.error(f"❌ Error ejecutando consulta: {error}", exc_info=True)
        logger.error(f"Consulta fallida: {query}")
        return None

# todo: una vez que tenga la base de datos armada, crear los métodos para crear tablas e insertar datos