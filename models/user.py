from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

class UserBase(BaseModel):
    nombre: str = Field(..., min_length=2)
    apellido: str = Field(..., min_length=2)
    dni: str = Field(..., min_length=7)
    cuil_cuit: str = Field(..., min_length=11, max_length=13)
    email: EmailStr = Field(...,)
    telefono: str = Field(..., min_length=10)
    # cantidad_personas eliminado

class UserCreate(UserBase):
    password: str  # se agrega porque en el registro sí lo necesitás

class UserInDB(UserBase):
    id: int
    fecha_registro: datetime
    activo: bool = True

    class Config:
        from_attributes = True  

class UserResponse(UserBase):
    id: int
    fecha_registro: datetime
    activo: bool
