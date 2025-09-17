from fastapi import APIRouter, Form, HTTPException
from models.user import UserCreate, UserResponse
from config.database_operations import insert_usuario 
from pydantic import EmailStr
from datetime import datetime

router = APIRouter()

@router.post("/crear", response_model=UserResponse)
async def crear_usuario(
    nombre: str = Form(...),
    apellido: str = Form(...),
    dni: str = Form(...),
    email: EmailStr = Form(...),
    telefono: str = Form(...),
    password: str = Form(...,)
):
    user_data = UserCreate(
        nombre=nombre,
        apellido=apellido,
        dni=dni,
        email=email,
        telefono=telefono,
        password=password
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