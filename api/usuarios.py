from fastapi import APIRouter, HTTPException, status
import psycopg2
from psycopg2.extras import RealDictCursor
from config.logging_config import logger
from config.database_operations import execute_query
from config.database_config import get_database_config, validate_database_config
from pydantic import BaseModel
from typing import List
import os

DB_CONFIG = get_database_config()

is_valid, validation_msg = validate_database_config(DB_CONFIG)
if not is_valid:
    logger.error(f"Falló en la configuración de la base de datos: {validation_msg}")
else:
    logger.info("Configuración de la base de datos válida")


# Pydantic models
class UserListResponse(BaseModel):
    id: int
    nombre: str
    apellido: str
    email: str

    class Config: # para uso de un ORM
        from_attributes = True

class UserUpdateRequest(BaseModel):
    nombre: str
    apellido: str
    email: str

router = APIRouter()

# GET /api/usuarios - Listar todos los usuarios
@router.get("/usuarios", response_model=List[UserListResponse])
async def get_usuarios():
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        query = """
            SELECT id, nombre, apellido, email
            FROM usuarios
            WHERE activo = true
            ORDER BY id
        """
        usuarios = execute_query(cursor, query)
        cursor.close()
        connection.close()
        logger.info("Lista de usuarios consultada")
        return usuarios
    except Exception as e:
        logger.error(f"Error en GET /api/usuarios: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al obtener usuarios")

# DELETE /api/usuarios/{user_id} - Eliminar un usuario por ID
@router.delete("/usuarios/{user_id}")
async def delete_usuario(user_id: int):
    logger.info(f"DELETE request received for user_id: {user_id}")
    try:
        # Verificar que el usuario existe y está activo
        logger.info("Connecting to database...")
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor(cursor_factory=RealDictCursor)

        # Primero verificar si el usuario existe
        logger.info(f"Checking if user {user_id} exists and is active...")
        cursor.execute("SELECT id, nombre, apellido FROM usuarios WHERE id = %s AND activo = true", (user_id,))
        user = cursor.fetchone()
        logger.info(f"User query result: {user}")
        if not user:
            cursor.close()
            connection.close()
            logger.warning(f"User {user_id} not found or not active")
            raise HTTPException(status_code=404, detail="Usuario no encontrado")


        # Verificar si el usuario tiene reservas activas
        logger.info(f"Revisando reservas activas para el usuario con ID: {user_id}...")
        query = """
            SELECT COUNT(*) FROM reservas
            WHERE usuario_id = %s AND estado NOT IN ('Cancelada', 'Finalizada')
        """
        logger.info(f"Ejecutando consulta {query.strip()} para usuario con ID: {user_id}")
        cursor.execute(query, (user_id,))
        logger.info("Consulta exitosa")
        result = cursor.fetchone()
        logger.info(f"cursor.fetchone(): {result}")
        if result is None:
            logger.error("cursor.fetchone() retorna None - tno deberia pasar con COUNT(*)")
            active_reservations = 0
        else:
            active_reservations = result['count']
        logger.info(f"Reservas activas: {active_reservations}")
        if active_reservations > 0:
            cursor.close()
            connection.close()
            logger.warning(f"No se puede eliminar al usuario: {user_id} - tiene {active_reservations} reservas activas")
            raise HTTPException(status_code=400, detail="No se puede eliminar un usuario con reservas activas")

        # Marcar usuario como inactivo (soft delete)
        logger.info(f"Usuario inactivo {user_id}...")
        cursor.execute("UPDATE usuarios SET activo = false WHERE id = %s", (user_id,))
        connection.commit()
        logger.info(f"Usuario {user_id} inactivo")

        cursor.close()
        connection.close()

        logger.info(f"Usuario eliminado: {user_id} ({user['nombre']} {user['apellido']})")
        return {"message": f"Usuario {user['nombre']} {user['apellido']} eliminado exitosamente"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en DELETE /api/usuarios/{user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al eliminar usuario")

# PUT /api/usuarios/{user_id} - Editar datos de un usuario
@router.put("/usuarios/{user_id}")
async def update_usuario(user_id: int, user_data: UserUpdateRequest):
    logger.info(f"PUT request received for user_id: {user_id}")
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor(cursor_factory=RealDictCursor)

        # Verificar que el usuario existe y está activo
        cursor.execute("SELECT id FROM usuarios WHERE id = %s AND activo = true", (user_id,))
        user = cursor.fetchone()
        if not user:
            cursor.close()
            connection.close()
            logger.warning(f"User {user_id} not found or not active")
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Verificar que el email no esté siendo usado por otro usuario activo
        cursor.execute("SELECT id FROM usuarios WHERE email = %s AND activo = true AND id != %s", (user_data.email, user_id))
        existing_user = cursor.fetchone()
        if existing_user:
            cursor.close()
            connection.close()
            logger.warning(f"Email {user_data.email} already in use by another active user")
            raise HTTPException(status_code=400, detail="El email ya está en uso por otro usuario")

        # Actualizar el usuario
        cursor.execute("""
            UPDATE usuarios
            SET nombre = %s, apellido = %s, email = %s
            WHERE id = %s
        """, (user_data.nombre, user_data.apellido, user_data.email, user_id))
        connection.commit()

        cursor.close()
        connection.close()

        logger.info(f"Usuario actualizado: {user_id}")
        return {"message": "Usuario actualizado exitosamente"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en PUT /api/usuarios/{user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al actualizar usuario")