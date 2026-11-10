from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class GenerarTomas(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id_dieta: int = Field(gt=0)
    fecha_hasta: date | None = None
