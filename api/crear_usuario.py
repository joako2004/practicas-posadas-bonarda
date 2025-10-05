from fastapi import APIRouter, HTTPException
from models.user import UserCreate, UserResponse
from config.database_operations import insert_usuario
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta, timezone
from config.logging_config import logger
import bcrypt
import jwt
import os

SECRET_KEY = os.getenv('JWT_SECRET', 'tu_jwt_secreto')
ALGORITHM = 'HS256'

class UserCreateRequest(BaseModel):
    nombre: str
    apellido: str
    dni: str
    cuil_cuit: str
    email: EmailStr
    telefono: str
    password: str

router = APIRouter()

@router.post("/crear")
async def crear_usuario(request: UserCreateRequest):
    try:
        password = request.password

        logger.info(f'Password received: {repr(password)}, len chars: {len(password)}, len bytes: {len(password.encode("utf-8"))}')

        # Validar longitud en caracteres
        if len(password) > 72:
            raise HTTPException(
                status_code=400,
                detail='La contraseña no puede tener más de 72 caracteres'
            )

        # Validación corregida
        if len(password) < 8:
            raise HTTPException(
                status_code=400,
                detail='La contraseña debe tener al menos 8 caracteres'
            )

        # Truncar a 72 bytes para evitar error de bcrypt
        password = password.encode('utf-8')[:72].decode('utf-8', errors='replace')

        logger.info(f'Password after truncate: {repr(password)}, len chars: {len(password)}, len bytes: {len(password.encode("utf-8"))}')

        # Hash la contraseña
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # CRÍTICO: Usar la contraseña hasheada
        user_data = UserCreate(
            nombre=request.nombre,
            apellido=request.apellido,
            dni=request.dni,
            cuil_cuit=request.cuil_cuit,
            email=request.email,
            telefono=request.telefono,
            password=hashed_password
        )
        
        user_id = insert_usuario(user_data)

        if not user_id:
            raise HTTPException(status_code=500, detail="Error creando usuario")

        # Generar token JWT
        token_data = {"sub": str(user_id), "exp": datetime.now(timezone.utc) + timedelta(days=30)}
        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

        logger.info(f'Usuario creado exitosamente con ID {user_id}')
        
        # Log para debugging - construir respuesta paso a paso
        try:
            logger.info(f'Construyendo UserResponse con id={user_id}')
            logger.info(f'user_data.model_dump(exclude={{password}}): {user_data.model_dump(exclude={"password"})}')
            
            user_response = UserResponse(
                id=user_id,
                **user_data.model_dump(exclude={'password'}),
                activo=True,
                fecha_registro=datetime.now(timezone.utc)
            )
            logger.info(f'UserResponse creado exitosamente: {user_response}')
            
            response_dict = {
                "user": user_response,
                "token": token
            }
            logger.info(f'Response dict creado: {type(response_dict)}')
            
            return response_dict
        except Exception as e:
            logger.error(f'Error construyendo respuesta: {type(e).__name__}: {str(e)}')
            logger.error(f'Traceback completo:', exc_info=True)
            raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error en registro: {e}') 
        raise HTTPException(
            status_code=500,
            detail='Error interno del servidor. Por favor, intenta de nuevo'
        )