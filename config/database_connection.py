# ==========================================
# config/database_connection.py - Gestión de conexiones PostgreSQL
# ==========================================
import psycopg2
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from .logging_config import logger, log_database_connection
from .database_config import get_database_config, validate_database_config

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
        admin_connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT) # "ISOLATION_LEVEL_AUTOCOMMIT" se encarga de commitear las operaciones automáticamente
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

        # Obtener y validar configuración
        config = get_database_config()
        is_valid, validation_message = validate_database_config(config)

        if not is_valid:
            logger.error(f"❌ Configuración inválida: {validation_message}")
            return None, None

        # Log de configuración (sin password)
        logger.info(f"📋 Configuración cargada:")
        logger.info(f"   - Host: {config['host']}")
        logger.info(f"   - Database: {config['database']}")
        logger.info(f"   - User: {config['user']}")
        logger.info(f"   - Port: {config['port']}")
        logger.info(f"   - Password: {'*' * len(config['password']) if config['password'] else 'NOT SET'}")

        # Verificar y crear la base de datos si no existe
        logger.info('Verificando existencia de la base de datos...')
        if not verify_and_create_database(
            config['host'],
            config['user'],
            config['password'],
            config['port'],
            config['database']
        ):
            logger.error('No se pudo verificar/crear la base de datos')
            log_database_connection(False, '- Database verification failed')
            return None, None

        # Conectar a la base de datos específica
        logger.info(f'Conectando a la base de datos "{config["database"]}"...')
        connection = psycopg2.connect(**config) # desempaquetar el objeto para obtener los atributos para la conexión

        # Crear cursor para ejecutar consultas
        cursor = connection.cursor()

        # Verificar la conexión
        cursor.execute('SELECT version();')
        version = cursor.fetchone()
        logger.info("✅ Conexión exitosa a PostgreSQL")
        logger.info(f"Versión del servidor: {version[0]}")

        log_database_connection(True, f'- Connected to "{config["database"]}"')

        return connection, cursor

    except (Exception, Error) as error:
        logger.error(f"Error al conectar con PostgreSQL: {error}", exc_info=True)
        log_database_connection(False, f"- Connection error: {error}")

        # Ayuda específica para errores comunes
        if "authentication failed" in str(error).lower():
            logger.error("💡 Verifica que DB_PASSWORD esté configurado correctamente")
        elif "connection refused" in str(error).lower():
            logger.error("💡 Verifica que DB_HOST y DB_PORT sean correctos")
        elif "database" in str(error).lower() and "does not exist" in str(error).lower():
            logger.error("💡 Verifica que DB_NAME sea correcto")

        return None, None

def verify_active_connection(connection):
    """
    Verifica si la conexión a la base de datos está activa
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

def close_connection(connection, cursor):
    """
    Cierra la conexión a la base de datos de forma segura
    """
    try:
        if cursor:
            cursor.close()
            logger.debug("Cursor cerrado exitosamente")
        if connection:
            connection.close()
            logger.info("🔌 Conexión a base de datos cerrada exitosamente")
            log_database_connection(True, "- Connection closed safely")

        logger.info("Recursos de base de datos liberados correctamente")

    except Error as error:
        logger.warning(f"⚠️ Error cerrando conexión: {error}")
        log_database_connection(False, f"- Close error: {error}")

def get_connection_stats():
    """
    Función utilitaria para obtener estadísticas de la base de datos
    """
    conn, cur = connect_postgresql()

    if not conn or not cur:
        logger.error("No se pudo obtener estadísticas - conexión fallida")
        return None

    try:
        # Obtener información de la base de datos
        stats = {}

        # Versión de PostgreSQL
        cur.execute("SELECT version()")
        stats['version'] = cur.fetchone()[0]

        # Número de conexiones activas
        cur.execute("SELECT count(*) FROM pg_stat_activity")
        stats['active_connections'] = cur.fetchone()[0]

        # Tamaño de la base de datos
        cur.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
        stats['database_size'] = cur.fetchone()[0]

        # Estadísticas específicas del sistema de posada
        cur.execute("SELECT COUNT(*) FROM usuarios WHERE activo = TRUE")
        stats['usuarios_activos'] = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM reservas")
        stats['total_reservas'] = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM habitaciones WHERE disponible = TRUE")
        stats['habitaciones_disponibles'] = cur.fetchone()[0]

        logger.info(f"📊 Estadísticas de base de datos obtenidas: {stats}")
        return stats

    except Error as error:
        logger.error(f"❌ Error obteniendo estadísticas: {error}")
        return None

    finally:
        close_connection(conn, cur)