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
            query = f'INSERT INTO {table} (nombre, apellido, dni, email, telefono) VALUES (%s, %s, %s, %s, %s) RETURNING id'

        logger.debug(f'Ejecutando inserción en tabla "{table}": {query}')
        cursor.execute(query, data)
        new_id = cursor.fetchone()[0] 
        connection.commit()

        logger.info(f"✅ Datos insertados correctamente en tabla '{table}' con ID: {new_id}")
        return new_id

    except Error as error:
        logger.error(f"❌ Error insertando datos en tabla '{table}': {error}", exc_info=True)
        connection.rollback()
        logger.warning("⚠️ Transacción revertida debido al error")
        return False

# Funciones auxiliares para operaciones específicas del sistema

def insert_usuario(user_data):
    """Inserta un nuevo usuario usando el objeto UserCreate"""
    try:
        from .database_connection import connect_postgresql, close_connection

        logger.info(f"🔍 DIAGNOSTIC - insert_usuario called with user_data type: {type(user_data)}")
        connection, cursor = connect_postgresql()
        logger.info(f"🔍 DIAGNOSTIC - Database connection result: connection={connection is not None}, cursor={cursor is not None}")
        
        if not connection or not cursor:
            logger.error("🔍 DIAGNOSTIC - Database connection FAILED - returning error dict")
            return {"error": "Database connection failed", "type": "connection_error"}

        cursor.execute("""
            INSERT INTO usuarios (nombre, apellido, dni, cuil_cuit, email, telefono, password, activo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            user_data.nombre,
            user_data.apellido,
            user_data.dni,
            user_data.cuil_cuit,
            user_data.email,
            user_data.telefono,
            user_data.password,
            True
        ))

        result = cursor.fetchone()
        if result is None:
            raise ValueError("No se pudo obtener el ID del usuario insertado")
        user_id = result[0]
        connection.commit()
        logger.info(f"Usuario creado con ID: {user_id}")
        logger.info(f"🔍 DIAGNOSTIC - User successfully inserted with ID: {user_id}")
        return user_id

    except Exception as error:
        logger.error(f"🔍 DIAGNOSTIC - Exception caught in insert_usuario: type={type(error).__name__}, message={str(error)}")
        logger.error(f"Error insertando usuario: {error}")
        if 'connection' in locals() and connection:
            connection.rollback()

        error_str = str(error)
        if 'UniqueViolation' in str(type(error)) or ('psycopg2' in str(type(error)) and 'IntegrityError' in error_str):
            logger.error("DEBUG: Unique constraint violation detected")
            if 'email' in error_str.lower():
                return {"error": "El email ya está registrado", "type": "duplicate_email"}
            elif 'dni' in error_str.lower():
                return {"error": "El DNI ya está registrado", "type": "duplicate_dni"}
            elif 'cuil_cuit' in error_str.lower():
                return {"error": "El CUIL/CUIT ya está registrado", "type": "duplicate_cuil_cuit"}
            elif 'telefono' in error_str.lower():
                return {"error": "El teléfono ya está registrado", "type": "duplicate_telefono"}
            elif 'nombre' in error_str.lower() and 'apellido' in error_str.lower():
                return {"error": "Ya existe un usuario con el mismo nombre y apellido", "type": "duplicate_nombre_apellido"}
            else:
                return {"error": "Violación de restricción de unicidad", "type": "duplicate_constraint", "details": error_str}
        else:
            return {"error": "Error interno del servidor", "type": "internal_error", "details": error_str}
    finally:
        if 'connection' in locals() and 'cursor' in locals():
            close_connection(connection, cursor)

def insert_reserva(cursor, connection, usuario_id, fecha_check_in, fecha_check_out,
                  cantidad_habitaciones, precio_total, observaciones=""):
    """
    Inserta una nueva reserva - VERSIÓN CORREGIDA
    """
    try:
        cursor.execute("SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'reservas' AND column_name = 'observaciones'")
        observaciones_exists = cursor.fetchone()[0] > 0

        logger.debug(f"📋 Verificación de columna 'observaciones' en tabla 'reservas': {'EXISTS' if observaciones_exists else 'NOT EXISTS'}")

        if observaciones_exists:
            cursor.execute("""
                INSERT INTO reservas (usuario_id, fecha_check_in, fecha_check_out,
                                    cantidad_habitaciones, precio_total, observaciones)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (usuario_id, fecha_check_in, fecha_check_out, cantidad_habitaciones,
                  precio_total, observaciones))
            logger.debug("✅ INSERT con columna 'observaciones' ejecutado")
        else:
            cursor.execute("""
                INSERT INTO reservas (usuario_id, fecha_check_in, fecha_check_out,
                                    cantidad_habitaciones, precio_total)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (usuario_id, fecha_check_in, fecha_check_out, cantidad_habitaciones,
                  precio_total))
            logger.warning("⚠️ INSERT sin columna 'observaciones' - columna no existe en tabla")

        reserva_id = cursor.fetchone()[0]  
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

def get_user_by_id(user_id):
    """Obtiene un usuario por ID"""
    try:
        from .database_connection import connect_postgresql, close_connection
        
        connection, cursor = connect_postgresql()
        if not connection or not cursor:
            logger.error("No se pudo conectar a la base de datos")
            return None
        
        cursor.execute("""
            SELECT id, nombre, apellido, email, activo
            FROM usuarios
            WHERE id = %s AND activo = true
        """, (user_id,))
        
        user = cursor.fetchone()
        if not user:
            return None
        
        user_id, nombre, apellido, email, activo = user
        user_data = {
            'id': user_id,
            'nombre': nombre,
            'apellido': apellido,
            'email': email,
            'activo': activo
        }
        return user_data
            
    except Exception as error:
        logger.error(f"Error obteniendo usuario por ID: {error}")
        return None
    finally:
        if 'connection' in locals() and 'cursor' in locals():
            close_connection(connection, cursor)
    
def authenticate_user(identifier, password):
    """Autentica un usuario por email o DNI y contraseña"""
    try:
        from .database_connection import connect_postgresql, close_connection
        import bcrypt
        
        connection, cursor = connect_postgresql()
        if not connection or not cursor:
            logger.error("No se pudo conectar a la base de datos")
            return None
        
        # Buscar por email o DNI
        cursor.execute("""
            SELECT id, nombre, apellido, dni, email, activo, password
            FROM usuarios
            WHERE (LOWER(email) = LOWER(%s) OR dni = %s) AND activo = true
        """, (identifier, identifier))

        user = cursor.fetchone()
        if not user:
            logger.warning(f"Intento de login fallido: Usuario {identifier} no encontrado")
            return None

        user_id, nombre, apellido, dni, email_db, activo, hashed_password = user

        try:
            password_bytes = password.encode('utf-8')
            hashed_password_bytes = hashed_password.encode('utf-8')

            password_match = bcrypt.checkpw(password_bytes, hashed_password_bytes)

            if not password_match:
                logger.warning(f"Intento de login fallido: contraseña incorrecta para {identifier}")
                return None

        except Exception as e:
            logger.error(f"Error verificando contraseña: {e}")
            return None
        
        user_data = {
            'id': user_id,
            'nombre': nombre,
            'apellido': apellido,
            'dni': dni,
            'email': email_db,
            'activo': activo
        }
        logger.info(f"Usuario autenticado exitosamente: {identifier}")
        return user_data
            
    except Exception as error:
        logger.error(f"Error autenticando usuario: {error}")
        return None
    finally:
        if 'connection' in locals() and 'cursor' in locals():
            close_connection(connection, cursor)