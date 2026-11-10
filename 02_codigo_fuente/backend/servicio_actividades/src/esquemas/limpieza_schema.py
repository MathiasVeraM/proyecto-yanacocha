from datetime import date, time

from pydantic import BaseModel, ConfigDict, Field, model_validator


class LimpiezaCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    id_recinto: int = Field(gt=0)
    fecha_programada: date
    hora_programada: time | None = None
    duracion_horas: int = Field(default=0, ge=0, le=32767)
    duracion_minutos: int = Field(default=0, ge=0, le=59)
    observaciones: str | None = None

    @model_validator(mode="after")
    def validar_duracion(self):
        if self.duracion_horas * 60 + self.duracion_minutos <= 0:
            raise ValueError("La limpieza requiere duración mayor que cero")
        return self
