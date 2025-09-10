from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional

class PriceBase(BaseModel):
    precio_por_noche: int = Field(..., gt=0)

class PriceCreate(PriceBase):
    pass

class PriceInDB(PriceBase):
    id: int
    
    class Config:
        from_attributes = True  

class PriceResponse(PriceInDB):
    pass


