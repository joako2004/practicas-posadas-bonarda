# ==========================================
# config/database.py - Conexión PostgreSQL con variables de entorno
# ==========================================
import os
import psycopg2
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from logging_config import *

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
        
        # Obtener y validar configuración
        config = get_database_config()
        is_valid, validation_message = validate_database_config(config)
        
        if not is_valid:
            logger.error(f"❌ Configuración inválida: {validation_message}")
            return None, None
        
        # Log de configuración 
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
        connection = psycopg2.connect(**config)
        
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

def insert_data(cursor, connection, table, data, columns=None):
    """
    Inserta datos en una tabla y retorna el ID del registro creado
    """
    try:
        if columns:
            placeholders = ', '.join(['%s'] * len(data))
            columns_str = ', '.join(columns)
            query = f'INSERT INTO {table} ({columns_str}) VALUES ({placeholders}) RETURNING id'
        else:
            query = f'INSERT INTO {table} (nombre, apellido, dni, email, telefono, cantidad_personas) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id'
        
        logger.debug(f'Ejecutando inserción en tabla "{table}": {query}')
        cursor.execute(query, data)
        new_id = cursor.fetchone()[0]  # Obtener el ID antes del commit
        connection.commit()

        logger.info(f"✅ Datos insertados correctamente en tabla '{table}' con ID: {new_id}")
        return new_id
    
    except Error as error:
        logger.error(f"❌ Error insertando datos en tabla '{table}': {error}", exc_info=True)
        connection.rollback()
        logger.warning("⚠️ Transacción revertida debido al error")
        return False

def create_default_rooms(cursor, connection):
    """
    Crea las 4 habitaciones de la posda si no existen
    """
    try:
        logger.info('🏠 Inicializando habitaciones por defecto...')
        
        # Verificar si ya existen habitaciones
        cursor.execute('SELECT COUNT(*) FROM habitaciones')
        existing_rooms = cursor.fetchone()[0]
        
        if existing_rooms == 0:
            habitaciones_data = [
                (1, 'Habitación 1'),
                (2, 'Habitación 2'),
                (3, 'Habitación 3'),
                (4, 'Habitación 4')
            ]
        
            for numero, descripcion in habitaciones_data:
                cursor.execute(
                    'INSERT INTO habitaciones (numero, descripcion) VALUES (%s, %s)',
                    (numero, descripcion)
                )
            
            connection.commit()
            logger.info(f"✅ Se crearon {len(habitaciones_data)} habitaciones por defecto")
        else:
            logger.info(f"ℹ️ Ya existen {existing_rooms} habitaciones en el sistema")
        
        return True
    
    except Error as error:
        logger.error(f"❌ Error creando habitaciones por defecto: {error}", exc_info=True)    
        connection.rollback()
        return False

def create_posada_tables(cursor, connection):
    """
    Crea todas las tablas necesarias para el sistema
    """
    tables = {
        'usuarios': """
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            apellido VARCHAR(100) NOT NULL,
            dni VARCHAR(20) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            telefono VARCHAR(20),
            cantidad_personas INTEGER NOT NULL DEFAULT 1,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            activo BOOLEAN DEFAULT TRUE
        )
        """,
        
        'habitaciones': """
        CREATE TABLE IF NOT EXISTS habitaciones (
            id SERIAL PRIMARY KEY,
            numero INTEGER UNIQUE NOT NULL CHECK (numero BETWEEN 1 AND 4),
            descripcion VARCHAR(255) DEFAULT 'Habitación estándar de la posada',
            disponible BOOLEAN DEFAULT TRUE,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        'precios': """
        CREATE TABLE IF NOT EXISTS precios (
            id SERIAL PRIMARY KEY,
            precio_por_noche DECIMAL(10,2) NOT NULL CHECK (precio_por_noche > 0)
        )
        """,
        
        'reservas': """
        CREATE TABLE IF NOT EXISTS reservas (
            id SERIAL PRIMARY KEY,
            usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            fecha_check_in DATE NOT NULL,
            fecha_check_out DATE NOT NULL,
            cantidad_habitaciones INTEGER NOT NULL DEFAULT 1 CHECK (cantidad_habitaciones BETWEEN 1 AND 4),
            precio_total DECIMAL(10,2) NOT NULL CHECK (precio_total >= 0),
            estado VARCHAR(20) NOT NULL DEFAULT 'pendiente' 
                CHECK (estado IN ('pendiente', 'confirmada', 'cancelada', 'finalizada')),            
        )
        """,
        
        'reserva_habitaciones': """
        CREATE TABLE IF NOT EXISTS reserva_habitaciones (
            id SERIAL PRIMARY KEY,
            reserva_id INTEGER NOT NULL REFERENCES reservas(id) ON DELETE CASCADE,
            habitacion_id INTEGER NOT NULL REFERENCES habitaciones(id) ON DELETE RESTRICT,
            fecha_asignacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(reserva_id, habitacion_id)
        )
        """,
        
        'pagos': """
        CREATE TABLE IF NOT EXISTS pagos (
            id SERIAL PRIMARY KEY,
            reserva_id INTEGER NOT NULL REFERENCES reservas(id) ON DELETE CASCADE,
            tipo_pago VARCHAR(20) NOT NULL 
                CHECK (tipo_pago IN ('seña', 'pago_completo')),
            monto DECIMAL(10,2) NOT NULL CHECK (monto > 0),
            metodo_pago VARCHAR(20) NOT NULL 
                CHECK (metodo_pago IN ('efectivo', 'transferencia', 'tarjeta_debito', 'tarjeta_credito')),
            estado_pago VARCHAR(15) NOT NULL DEFAULT 'pendiente'
                CHECK (estado_pago IN ('pendiente', 'pagado', 'reembolsado')),
            fecha_pago TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            comprobante VARCHAR(255),
            observaciones TEXT
        )
        """
    }
    
    logger.info("🏗️ Iniciando creación de tablas del sistema de posada...")
    created_tables = 0

    try:
        for table_name, sql in tables.items():
            logger.debug(f'Creando tabla {table_name}')
            cursor.execute(sql)
            created_tables += 1
            logger.debug(f'✅ Tabla "{table_name}" procesada correctamente')
        
        connection.commit()
        logger.info(f"✅ Todas las tablas del sistema creadas/verificadas exitosamente ({created_tables} tablas)")
        
        # Crear las 4 habitaciones si no existen
        if create_default_rooms(cursor, connection):
            logger.info('✅ Habitaciones por defecto inicializadas')
        
        return True
    
    except Error as error:
        logger.error(f"❌ Error creando tablas del sistema: {error}", exc_info=True)
        connection.rollback()
        return False

def create_default_price(cursor, connection, precio_inicial=50000.00):
    """
    Crea un precio inicial por defecto si no existe ningún precio activo
    """
    try:
        logger.info("💰 Verificando precios por defecto...")
        
        cursor.execute("SELECT COUNT(*) FROM precios WHERE activo = TRUE")
        active_prices = cursor.fetchone()[0]
        
        if active_prices == 0:
            cursor.execute("""
                INSERT INTO precios (precio_por_noche, fecha_vigencia_desde, descripcion)
                VALUES (%s, CURRENT_DATE, %s)
            """, (precio_inicial, "Precio inicial del sistema"))
            connection.commit()
            logger.info(f"✅ Precio inicial creado: ${precio_inicial} por noche")
        else:
            logger.info(f"ℹ️ Ya existen {active_prices} precios activos")
            
        return True
    except Error as error:
        logger.error(f"❌ Error creando precio: {error}", exc_info=True)
        connection.rollback()
        return False

def initialize_posada_system(cursor, connection):
    """
    Inicializa completamente el sistema de la posada:
    - Crea todas las tablas
    - Inicializa habitaciones
    - Crea precio por defecto
    """
    logger.info("🚀 Inicializando sistema completo de la posada...")
    
    try:
        # Paso 1: Crear todas las tablas
        if not create_posada_tables(cursor, connection):
            logger.error("❌ Falló la creación de tablas")
            return False
        
        # Paso 2: Crear precio por defecto
        if not create_default_price(cursor, connection):
            logger.error("❌ Falló la creación del precio por defecto")
            return False
        
        logger.info("🎉 Sistema de posada inicializado correctamente")
        logger.info("📋 Resumen del sistema:")
        logger.info("   - ✅ 6 tablas creadas (usuarios, habitaciones, reservas, etc.)")
        logger.info("   - ✅ 4 habitaciones inicializadas")
        logger.info("   - ✅ Precio por defecto establecido")
        logger.info("   - ✅ Restricciones y validaciones aplicadas")
        
        return True
        
    except Exception as error:
        logger.error(f"❌ Error en inicialización del sistema: {error}", exc_info=True)
        return False

# Funciones auxiliares para operaciones específicas del sistema

def insert_usuario(cursor, connection, nombre, apellido, dni, email, telefono, cantidad_personas):
    """
    Inserta un nuevo usuario con validaciones específicas
    """
    try:
        data = (nombre, apellido, dni, email, telefono, cantidad_personas)
        columns = ['nombre', 'apellido', 'dni', 'email', 'telefono', 'cantidad_personas']
        
        return insert_data(cursor, connection, 'usuarios', data, columns)
        
    except Exception as error:
        logger.error(f"❌ Error insertando usuario: {error}")
        return False

def insert_reserva(cursor, connection, usuario_id, fecha_check_in, fecha_check_out, 
                  cantidad_habitaciones, precio_total, observaciones=""):
    """
    Inserta una nueva reserva - VERSIÓN CORREGIDA
    """
    try:
        # ✅ Inserción directa con RETURNING - MÁS SEGURA
        cursor.execute("""
            INSERT INTO reservas (usuario_id, fecha_check_in, fecha_check_out, 
                                cantidad_habitaciones, precio_total, observaciones)
            VALUES (%s, %s, %s, %s, %s, %s) 
            RETURNING id
        """, (usuario_id, fecha_check_in, fecha_check_out, cantidad_habitaciones, 
              precio_total, observaciones))
        
        reserva_id = cursor.fetchone()[0]  # ✅ ID correcto garantizado
        connection.commit()
        
        logger.info(f"✅ Reserva creada con ID: {reserva_id}")
        return reserva_id
        
    except Exception as error:
        connection.rollback()
        logger.error(f"❌ Error insertando reserva: {error}")
        return False

def insert_pago(cursor, connection, reserva_id, tipo_pago, monto, metodo_pago, comprobante=""):
    """
    Inserta un nuevo pago para una reserva
    """
    try:
        data = (reserva_id, tipo_pago, monto, metodo_pago, 'pagado', comprobante)
        columns = ['reserva_id', 'tipo_pago', 'monto', 'metodo_pago', 'estado_pago', 'comprobante']
        
        return insert_data(cursor, connection, 'pagos', data, columns)
        
    except Exception as error:
        logger.error(f"❌ Error insertando pago: {error}")
        return False

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

def get_environment_info():
    """
    NUEVA FUNCIÓN: Información sobre el entorno actual
    """
    
    env_info = {
        'environment': os.getenv('ENVIRONMENT', 'development'),
        'db_host': os.getenv('DB_HOST', 'localhost'),
        'db_name': os.getenv('DB_NAME', 'posada_db'),
        'db_user': os.getenv('DB_USER', 'postgres'),
        'db_port': os.getenv('DB_PORT', '5432'),
        'password_configured': bool(os.getenv('DB_PASSWORD')),
        'python_version': os.sys.version,
        'working_directory': os.getcwd()
    }
    
    logger.info("🌍 Información del entorno:")
    for key, value in env_info.items():
        logger.info(f'  -{key}: {value}')
    
    return env_info

#! Función auxiliar para debugging
def test_environment_setup():
    from dotenv import load_dotenv
    load_dotenv()   
    """
    NUEVA FUNCIÓN: Prueba la configuración del entorno
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


test_environment_setup()