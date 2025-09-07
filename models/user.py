from pydantic import BaseModel, Field
from datetime import datetime
class user(BaseModel):
    id: int
    nombre: str = Field(min_length=2)
    apellido: str = Field(min_length=2)
    dni: str = Field(min_length=7)
    email: str
    telefono: str 
    cantidad_personas: int = Field(ge=1)
    fecha_registro: datetime
    activo: bool = Field(default=False)

