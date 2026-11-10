from datetime import date, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


TipoEnriquecimiento = Literal["social", "sensorial", "alimenticio", "cognitivo"]


class EnriquecimientoCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    id_animal: int = Field(gt=0)
    tipo_enriquecimiento: TipoEnriquecimiento
    fecha_programada: date
    hora_programada: time
    descripcion_estimulo: str = Field(min_length=1)
    observaciones: str | None = None
