from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional

class RoomBase(BaseModel):
    numero: int = Field(..., ge=1, le=4)
    descripcion: Optional[str] = None
    disponible: bool = True
    
class RoomCreate(RoomBase):
    pass

class RoomInDB(RoomBase):
    id: int
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True

class RoomResponse(RoomInDB):
    pass