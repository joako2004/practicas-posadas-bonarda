from pydantic import BaseModel, Field, EmailStr, field_validator
from datetime import datetime
import re

class UserBase(BaseModel):
    nombre: str = Field(..., min_length=2)
    apellido: str = Field(..., min_length=2)
    dni: str = Field(..., min_length=7, max_length=8)  # DNI argentino 7-8 dígitos
    cuil_cuit: str = Field(..., min_length=11, max_length=13)
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
        if not cuil_limpio.isdigit() or len(cuil_limpio) != 11:
            raise ValueError('CUIL/CUIT debe tener 11 dígitos (XX-XXXXXXXX-X)')
        return v
    
    @field_validator('telefono')
    @classmethod
    def validar_telefono(cls, v):
        telefono_limpio = re.sub(r'[\s\-\(\)]', '', v)
        if not telefono_limpio.isdigit():
            raise ValueError('El teléfono debe contener solo números, espacios y guiones')
        return v

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    
    @field_validator('password')
    @classmethod
    def validar_password(cls, v):
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        if not re.search(r'[A-Z]', v):
            raise ValueError('La contraseña debe contener al menos una mayúscula')
        if not re.search(r'[a-z]', v):
            raise ValueError('La contraseña debe contener al menos una minúscula')
        if not re.search(r'\d', v):
            raise ValueError('La contraseña debe contener al menos un número')
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