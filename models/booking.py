from pydantic import BaseModel, Field, model_validator
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum

class Estado(str, Enum):
    pendiente = "Pendiente"
    confirmado = "Confirmado"
    cancelada = "Cancelada"
    finalizada = "Finalizada"


class BookingBase(BaseModel):
    usuario_id: int = Field(..., ge=0)
    fecha_check_in: date
    fecha_check_out: date
    cantidad_habitaciones: int = Field(..., ge=1)


# lo que manda el cliente
class BookingCreate(BaseModel):
    fecha_check_in: date
    fecha_check_out: date
    cantidad_habitaciones: int = Field(..., ge=1)

    @model_validator(mode="after")
    def validate_date(self):
        if self.fecha_check_in >= self.fecha_check_out:
            raise ValueError("La fecha de check-out debe ser posterior a la de check-in")
        if (self.fecha_check_out - self.fecha_check_in).days < 2:
            raise ValueError("La reserva debe ser por al menos dos noches")
        return self


# lo que se guarda en la DB
class BookingInDB(BookingBase):
    id: int
    precio_total: Decimal
    estado: Estado = Estado.pendiente
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# lo que devuelve el backend
class BookingResponse(BookingInDB):
    pass
