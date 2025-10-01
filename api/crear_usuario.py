from fastapi import APIRouter, Form, HTTPException
from models.user import UserCreate, UserResponse
from config.database_operations import insert_usuario 
from pydantic import EmailStr
from datetime import datetime
from config.logging_config import logger
import bcrypt

router = APIRouter()

@router.post("/crear", response_model=UserResponse)
async def crear_usuario(
    nombre: str = Form(...),
    apellido: str = Form(...),
    dni: str = Form(...),
    cuil_cuit: str = Form(...),
    email: EmailStr = Form(...),
    telefono: str = Form(...),
    password: str = Form(...,)
):
    try:

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
            nombre=nombre,
            apellido=apellido,
            dni=dni,
            cuil_cuit=cuil_cuit,
            email=email,
            telefono=telefono,
            password=hashed_password  
        )
        
        user_id = insert_usuario(user_data)
        
        if not user_id:
            raise HTTPException(status_code=500, detail="Error creando usuario")
        
        logger.info(f'Usuario creado exitosamente con ID {user_id}')
        return UserResponse(
            id=user_id, 
            **user_data.model_dump(exclude={'password'}), 
            activo=True, 
            fecha_registro=datetime.now()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error en registro: {e}') 
        raise HTTPException(
            status_code=500,
            detail='Error interno del servidor. Por favor, intenta de nuevo'
        )