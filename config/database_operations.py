# ==========================================
# config/database_operations.py - Operaciones CRUD de base de datos
# ==========================================
from psycopg2 import Error
from .logging_config import logger

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
        # DEBUG: Check if 'observaciones' column exists in reservas table
        cursor.execute("SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'reservas' AND column_name = 'observaciones'")
        observaciones_exists = cursor.fetchone()[0] > 0

        logger.debug(f"📋 Verificación de columna 'observaciones' en tabla 'reservas': {'EXISTS' if observaciones_exists else 'NOT EXISTS'}")

        if observaciones_exists:
            # ✅ Inserción directa con RETURNING - MÁS SEGURA
            cursor.execute("""
                INSERT INTO reservas (usuario_id, fecha_check_in, fecha_check_out,
                                    cantidad_habitaciones, precio_total, observaciones)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (usuario_id, fecha_check_in, fecha_check_out, cantidad_habitaciones,
                  precio_total, observaciones))
            logger.debug("✅ INSERT con columna 'observaciones' ejecutado")
        else:
            # Fallback: INSERT without observaciones column
            cursor.execute("""
                INSERT INTO reservas (usuario_id, fecha_check_in, fecha_check_out,
                                    cantidad_habitaciones, precio_total)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (usuario_id, fecha_check_in, fecha_check_out, cantidad_habitaciones,
                  precio_total))
            logger.warning("⚠️ INSERT sin columna 'observaciones' - columna no existe en tabla")

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