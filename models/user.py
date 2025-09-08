from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    nombre: str = Field(..., min_length=2)
    apellido: str = Field(..., min_length=2)
    dni: str = Field(..., min_length=7)
    email: EmailStr
    telefono: str
    cantidad_personas: int = Field(..., ge=1)

class UserCreate(UserBase):
    pass  # igual a UserBase, pero separado por claridad

class UserInDB(UserBase):
    id: int
    fecha_registro: datetime
    activo: bool = True

    class Config:
        from_attributes = True  # permite mapear desde ORM si usás SQLAlchemy

class UserResponse(UserInDB):
    pass
