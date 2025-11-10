from pydantic import BaseModel, Field, EmailStr, field_validator
from datetime import datetime
import re

class UserBase(BaseModel):
    nombre: str = Field(..., min_length=2)
    apellido: str = Field(..., min_length=2)
    dni: str = Field(..., min_length=7, max_length=8)
    cuil_cuit: str = Field(..., min_length=10, max_length=13)
    email: EmailStr = Field(...)
    telefono: str = Field(..., min_length=8, max_length=15)
    
    @field_validator('dni')
    @classmethod
    def validar_dni(cls, v):
        if not v.isdigit():
            raise ValueError('El DNI debe contener solo números')
        return v
    
    @field_validator('cuil_cuit')
    @classmethod
    def validar_cuil_cuit(cls, v):
        cuil_limpio = v.replace('-', '').replace(' ', '')
        if not cuil_limpio.isdigit() or len(cuil_limpio) < 10 or len(cuil_limpio) > 13:
            raise ValueError('CUIL/CUIT debe tener entre 10 y 13 dígitos')
        return v
    
    @field_validator('telefono')
    @classmethod
    def validar_telefono(cls, v):
        telefono_limpio = re.sub(r'[\s\-\(\)]', '', v)
        if not telefono_limpio.isdigit():
            raise ValueError('El teléfono debe contener solo números, espacios y guiones')
        return v

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=72)  # Agregado max_length
    
    @field_validator('password')
    @classmethod
    def validar_password(cls, v):
        if len(v) > 72:
            raise ValueError('La contraseña debe tener menos de 72 caracteres')
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        if not (re.search(r'[A-Z]', v) and re.search(r'[a-z]', v)):
            raise ValueError('La contraseña debe contener al menos una mayúscula y una minúscula')
        # Comentado para permitir contraseñas sin números
        # if not re.search(r'\d', v):
        #     raise ValueError('La contraseña debe contener al menos un número')
        return v

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