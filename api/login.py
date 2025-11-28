from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from config.database_operations import authenticate_user
from config.logging_config import logger

router = APIRouter()

class LoginRequest(BaseModel):
    dni: str
    password: str

@router.post("/login")
async def login(request: LoginRequest):
    """
    Endpoint para autenticación de usuarios mediante DNI y contraseña
    """
    try:
        user = authenticate_user(request.dni, request.password)
        
        if not user:
            logger.warning(f"Intento de login fallido para DNI {request.dni}")
            raise HTTPException(
                status_code=401,
                detail="DNI o contraseña incorrectos"
            )
        
        logger.info(f"Login exitoso para usuario: {user['nombre']} {user['apellido']} (DNI: {user['dni']})")
        
        return {
            "message": "Login exitoso",
            "user": user
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en login: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )