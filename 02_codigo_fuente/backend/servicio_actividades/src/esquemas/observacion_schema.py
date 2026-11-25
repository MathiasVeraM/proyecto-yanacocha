from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


CategoriaObservacion = Literal["recinto", "comportamiento", "estado_fisico"]
SeveridadObservacion = Literal["bajo", "medio", "alto"]


class ObservacionCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    categoria: CategoriaObservacion
    severidad: SeveridadObservacion
    detalle: str = Field(min_length=10)
    # Solo los envía la app móvil: identificador único y hora real del dispositivo.
    id_cliente: str | None = Field(default=None, min_length=8, max_length=64)
    fecha_registro: datetime | None = None


class ObservacionResponse(BaseModel):
    id_observacion: int
    id_actividad: int
    categoria: str
    severidad: str
    detalle: str
    genera_alerta: bool
    id_usuario: int
    fecha_registro: datetime
    id_cliente: str | None = None

    model_config = ConfigDict(from_attributes=True)
