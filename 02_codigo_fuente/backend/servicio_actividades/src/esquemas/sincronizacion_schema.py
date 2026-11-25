from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from src.esquemas.observacion_schema import CategoriaObservacion, SeveridadObservacion

MAX_REGISTROS_LOTE = 200


class CompletadaSync(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=False, extra="ignore")

    id_actividad: int
    # Hora real del dispositivo al marcar la actividad (zona del centro).
    fecha_completada: datetime
    observaciones: str | None = None


class ObservacionSync(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    id_cliente: str = Field(min_length=8, max_length=64)
    id_actividad: int
    categoria: CategoriaObservacion
    severidad: SeveridadObservacion
    detalle: str = Field(min_length=10)
    fecha_registro: datetime


class SincronizacionRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    completadas: list[CompletadaSync] = Field(default_factory=list, max_length=MAX_REGISTROS_LOTE)
    observaciones: list[ObservacionSync] = Field(default_factory=list, max_length=MAX_REGISTROS_LOTE)


# creada:    se guardó ahora.
# duplicada: ya estaba guardada (reintento o ya completada por otra persona); no se toca.
# rechazada: no se puede guardar nunca (actividad borrada, fecha inválida...); la app la descarta.
ResultadoSync = Literal["creada", "duplicada", "rechazada"]


class ResultadoItemSync(BaseModel):
    id_actividad: int
    id_cliente: str | None = None
    resultado: ResultadoSync
    detalle: str | None = None


class SincronizacionResponse(BaseModel):
    completadas: list[ResultadoItemSync]
    observaciones: list[ResultadoItemSync]
