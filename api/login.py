from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from config.database_connection import connect_postgresql, close_connection
from config.logging_config import logger
import bcrypt

router = APIRouter()

class LoginRequest(BaseModel):
    dni: str
    password: str

@router.post("/login")
async def login(request: LoginRequest):
    """
    Endpoint para autenticación de usuarios mediante DNI y contraseña
    """
    connection = None
    cursor = None
    
    try:
        # Conectar a la base de datos
        connection, cursor = connect_postgresql()
        if not connection or not cursor:
            logger.error("No se pudo conectar a la base de datos")
            raise HTTPException(
                status_code=500,
                detail="Error de conexión con la base de datos"
            )
        
        # Buscar usuario por DNI
        cursor.execute("""
            SELECT id, nombre, apellido, dni, email, password, activo
            FROM usuarios
            WHERE dni = %s
        """, (request.dni,))
        
        user = cursor.fetchone()
        
        # Verificar si el usuario existe
        if not user:
            logger.warning(f"Intento de login fallido: DNI {request.dni} no encontrado")
            raise HTTPException(
                status_code=401,
                detail="DNI o contraseña incorrectos"
            )
        
        user_id, nombre, apellido, dni, email, hashed_password, activo = user
        
        # Verificar si el usuario está activo
        if not activo:
            logger.warning(f"Intento de login con usuario inactivo: DNI {request.dni}")
            raise HTTPException(
                status_code=401,
                detail="Usuario inactivo"
            )
        
        # Verificar la contraseña
        password_bytes = request.password.encode('utf-8')
        hashed_password_bytes = hashed_password.encode('utf-8')
        
        if not bcrypt.checkpw(password_bytes, hashed_password_bytes):
            logger.warning(f"Intento de login fallido: contraseña incorrecta para DNI {request.dni}")
            raise HTTPException(
                status_code=401,
                detail="DNI o contraseña incorrectos"
            )
        
        # Login exitoso
        logger.info(f"Login exitoso para usuario: {nombre} {apellido} (DNI: {dni})")
        
        return {
            "message": "Login exitoso",
            "user": {
                "id": user_id,
                "nombre": nombre,
                "apellido": apellido,
                "dni": dni,
                "email": email
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en login: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )
    finally:
        if connection and cursor:
            close_connection(connection, cursor)