from pydantic import BaseModel, Field
from datetime import datetime

class BookingRoomBase(BaseModel):
    reserva_id: int = Field(..., ge=1)
    habitacion_id: int = Field(..., ge=1)

class BookingRoomCreate(BookingRoomBase):
    pass

class BookingRoomInDB(BookingRoomBase):
    id: int
    assigned_at: datetime

    class Config:
        from_attributes = True

class BookingRoomResponse(BookingRoomInDB):
    pass
