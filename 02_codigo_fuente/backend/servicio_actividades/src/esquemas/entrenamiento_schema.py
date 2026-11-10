from datetime import date, time

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EntrenamientoCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    id_animal: int = Field(gt=0)
    fecha_programada: date
    hora_programada: time
    duracion_horas: int = Field(default=0, ge=0, le=32767)
    duracion_minutos: int = Field(default=0, ge=0, le=59)
    objetivo_entrenamiento: str = Field(min_length=1)
    tipo_refuerzo: str = Field(min_length=1, max_length=150)
    observaciones: str | None = None

    @model_validator(mode="after")
    def validar_duracion(self):
        if self.duracion_horas * 60 + self.duracion_minutos <= 0:
            raise ValueError("El entrenamiento requiere duración mayor que cero")
        return self
