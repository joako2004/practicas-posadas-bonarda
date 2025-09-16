# ==========================================
# config/database_initialization.py - Inicialización del esquema de base de datos
# ==========================================
from psycopg2 import Error
from .logging_config import logger

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
            precio_por_noche DECIMAL(10,2) NOT NULL CHECK (precio_por_noche > 0),
            fecha_vigencia_desde DATE DEFAULT CURRENT_DATE,
            descripcion VARCHAR(255) DEFAULT 'Precio estándar',
            activo BOOLEAN DEFAULT TRUE,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            observaciones TEXT,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

        # DEBUG: Registrar la estructura actual de la tabla de precios
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'precios' ORDER BY ordinal_position")
        columns = cursor.fetchall()
        logger.debug(f"📋 Columnas actuales en tabla 'precios': {[col[0] for col in columns]}")

        # Revisar si la columna "activo" existe antes de hacer la consulta
        cursor.execute("SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'precios' AND column_name = 'activo'")
        activo_exists = cursor.fetchone()[0] > 0

        if activo_exists:
            cursor.execute("SELECT COUNT(*) FROM precios WHERE activo = TRUE")
            active_prices = cursor.fetchone()[0]
            logger.debug(f"✅ Columna 'activo' existe, precios activos: {active_prices}")
        else:
            cursor.execute("SELECT COUNT(*) FROM precios")
            active_prices = cursor.fetchone()[0]
            logger.warning("⚠️ Columna 'activo' NO existe en tabla 'precios', consultando total de registros")

        if active_prices == 0:
            # Revisar si exiten las columnas necesarias antes de hacer un insert
            cursor.execute("SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'precios' AND column_name IN ('fecha_vigencia_desde', 'descripcion')")
            required_columns_exist = cursor.fetchone()[0] == 2

            if required_columns_exist:
                cursor.execute("""
                    INSERT INTO precios (precio_por_noche, fecha_vigencia_desde, descripcion)
                    VALUES (%s, CURRENT_DATE, %s)
                """, (precio_inicial, "Precio inicial del sistema"))
                logger.debug("✅ INSERT con columnas completas ejecutado")
            else:
                cursor.execute("""
                    INSERT INTO precios (precio_por_noche)
                    VALUES (%s)
                """, (precio_inicial,))
                logger.warning("⚠️ INSERT simplificado - faltan columnas 'fecha_vigencia_desde' y 'descripcion'")

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
    