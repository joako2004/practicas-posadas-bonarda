from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

class PaymentType(str, Enum):
    parcial = "seña"
    completo = "pago_completo"

class PaymentMethod(str, Enum):
    efectivo = "efectivo"
    transferencia = "transferencia"
    tarjeta_debito = "tarjeta_debito"
    tarjeta_credito = "tarjeta_credito"

class PaymentStatus(str, Enum):
    pendiente = "pendiente"
    pagado = "pagado"
    reembolsado = "reembolsado"


class PaymentBase(BaseModel):
    reserva_id: int = Field(..., ge=1)
    tipo_pago: PaymentType
    cantidad: Decimal = Field(..., gt=0)
    metodo_pago: PaymentMethod
    estado_pago: PaymentStatus = PaymentStatus.pendiente
    recibo: Optional[str] = None
    nota: Optional[str] = None


class PaymentCreate(PaymentBase):
    pass


class PaymentInDB(PaymentBase):
    id: int
    fecha_pago: datetime

    class Config:
        from_attributes = True


class PaymentResponse(PaymentInDB):
    pass
