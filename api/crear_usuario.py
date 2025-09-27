from fastapi import APIRouter, Form, HTTPException
from models.user import UserCreate, UserResponse
from config.database_operations import insert_usuario 
from pydantic import EmailStr
from datetime import datetime
from config.logging_config import logger
from passlib.context import CryptContext

router = APIRouter()

# Configuraciones para el hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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
        # Validación corregida
        if len(password) < 8:  # Cambiado de <= a 
            raise HTTPException(
                status_code=400,
                detail='La contraseña debe tener al menos 8 caracteres'
            )
    
        # Hash la contraseña
        hashed_password = pwd_context.hash(password)
        
        # CRÍTICO: Usar la contraseña hasheada
        user_data = UserCreate(
            nombre=nombre,
            apellido=apellido,
            dni=dni,
            cuil_cuit=cuil_cuit,
            email=email,
            telefono=telefono,
            password=hashed_password  # ✅ CORRECTO - usar el hash
        )
        
        user_id = insert_usuario(user_data)
        
        if not user_id:
            raise HTTPException(status_code=500, detail="Error creando usuario")
        
        return UserResponse(
            id=user_id, 
            **user_data.model_dump(exclude={'password'}), 
            activo=True, 
            fecha_registro=datetime.now()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error en registro: {e}')  # Typo corregido
        raise HTTPException(
            status_code=500,
            detail='Error interno del servidor'
        )