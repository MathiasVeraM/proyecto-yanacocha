from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


TipoActividad = Literal["alimentacion", "enriquecimiento", "entrenamiento", "limpieza"]


class ActividadBaseCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    tipo_actividad: TipoActividad
    id_animal: int | None = Field(default=None, gt=0)
    id_recinto: int | None = Field(default=None, gt=0)
    fecha_programada: date
    hora_programada: time | None = None
    duracion_horas: int = Field(default=0, ge=0, le=32767)
    duracion_minutos: int = Field(default=0, ge=0, le=59)
    observaciones: str | None = None
    id_dieta: int | None = Field(default=None, gt=0)
    tipo_enriquecimiento: str | None = None
    descripcion_estimulo: str | None = None
    objetivo_entrenamiento: str | None = None
    tipo_refuerzo: str | None = Field(default=None, max_length=150)

    @model_validator(mode="after")
    def validar_reglas_por_tipo(self):
        if self.tipo_actividad == "limpieza":
            if self.id_recinto is None:
                raise ValueError("La limpieza requiere id_recinto")
            if self.id_animal is not None:
                raise ValueError("La limpieza no puede asociarse a un animal")
            if self.duracion_horas * 60 + self.duracion_minutos <= 0:
                raise ValueError("La limpieza requiere duración mayor que cero")
        elif self.id_animal is None:
            raise ValueError("La actividad requiere id_animal")

        if self.tipo_actividad == "entrenamiento":
            if self.duracion_horas * 60 + self.duracion_minutos <= 0:
                raise ValueError("El entrenamiento requiere duración mayor que cero")
            if self.hora_programada is None:
                raise ValueError("El entrenamiento requiere hora_programada")
            if not self.objetivo_entrenamiento or not self.tipo_refuerzo:
                raise ValueError("El entrenamiento requiere objetivo y tipo de refuerzo")
        elif self.tipo_actividad == "enriquecimiento":
            if self.hora_programada is None:
                raise ValueError("El enriquecimiento requiere hora_programada")
            if self.tipo_enriquecimiento not in {
                "social",
                "sensorial",
                "alimenticio",
                "cognitivo",
            }:
                raise ValueError("Tipo de enriquecimiento no válido")
            if not self.descripcion_estimulo:
                raise ValueError("La descripción del estímulo es obligatoria")
        elif self.tipo_actividad == "alimentacion" and self.id_dieta is None:
            raise ValueError("La alimentación requiere id_dieta")
        return self


class AlimentacionCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    id_animal: int = Field(gt=0)
    id_dieta: int = Field(gt=0)
    fecha_programada: date
    hora_programada: time | None = None
    duracion_horas: int = Field(default=0, ge=0, le=32767)
    duracion_minutos: int = Field(default=0, ge=0, le=59)
    observaciones: str | None = None


class ActividadResponse(BaseModel):
    id_actividad: int
    tipo_actividad: str
    id_animal: int | None
    id_recinto: int | None
    fecha_programada: date
    hora_programada: time | None
    duracion_horas: int
    duracion_minutos: int
    id_usuario_programo: int
    fecha_registro: datetime
    completada: bool
    observaciones: str | None
    id_usuario_completo: int | None
    fecha_completada: datetime | None
    id_dieta: int | None = None
    tipo_enriquecimiento: str | None = None
    descripcion_estimulo: str | None = None
    objetivo_entrenamiento: str | None = None
    tipo_refuerzo: str | None = None
    id_tratamiento: int | None = None
    cancelada: bool = False

    model_config = ConfigDict(from_attributes=True)


class CompletarActividad(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=False, extra="ignore")

    observaciones: str | None = None


class EventoCalendario(BaseModel):
    id_actividad: int
    inicio: str
    fin: str
    tipo: str
    completada: bool
    todo_el_dia: bool


class Repeticion(BaseModel):
    """Cómo se repite una actividad: todos los días o ciertos días, hasta una fecha o N meses."""

    model_config = ConfigDict(extra="ignore")

    # 0 = lunes … 6 = domingo. Vacío o null = todos los días
    dias_semana: list[int] | None = None
    fecha_fin: date | None = None
    meses: int | None = Field(default=None, ge=1)


class ActividadRepetidaCreate(ActividadBaseCreate):
    repeticion: Repeticion


class ActividadUpdate(BaseModel):
    """Cambios de una actividad pendiente; solo se aplican los campos que se envían."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    fecha_programada: date | None = None
    hora_programada: time | None = None
    duracion_horas: int | None = Field(default=None, ge=0, le=32767)
    duracion_minutos: int | None = Field(default=None, ge=0, le=59)
    observaciones: str | None = None
    tipo_enriquecimiento: str | None = None
    descripcion_estimulo: str | None = None
    objetivo_entrenamiento: str | None = None
    tipo_refuerzo: str | None = Field(default=None, max_length=150)


class LimitesActividades(BaseModel):
    """Límites que el frontend usa como min y max de los campos (se definen en config.py)."""

    hoy: date
    hora_actual: time
    fecha_min: date
    fecha_max: date
    duracion_max_minutos: int
    duracion_enriquecimiento_minutos: int
    repeticion_meses_max: int
    dieta_inicio_fecha_max: date
