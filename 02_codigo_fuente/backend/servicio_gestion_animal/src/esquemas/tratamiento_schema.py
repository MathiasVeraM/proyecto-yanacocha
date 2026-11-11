from datetime import date, time
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


EstadoTratamiento = Literal["en_curso", "finalizado", "suspendido"]
FrecuenciaUnidad = Literal["horas", "dias"]


class TratamientoMedicamentoCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nombre_medicamento: str = Field(min_length=1, max_length=150)
    dosis_ml: Decimal = Field(gt=0, max_digits=8, decimal_places=2)


class TratamientoMedicamentoResponse(TratamientoMedicamentoCreate):
    id_tratamiento_medicamento: int

    model_config = ConfigDict(from_attributes=True)


class TratamientoCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    descripcion: str = Field(min_length=1)
    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    frecuencia_valor: int = Field(gt=0, le=2_147_483_647)
    frecuencia_unidad: FrecuenciaUnidad
    hora_inicio: time
    estado: EstadoTratamiento = "en_curso"
    medicamentos: list[TratamientoMedicamentoCreate] = Field(default_factory=list)


class TratamientoUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    descripcion: str | None = Field(default=None, min_length=1)
    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    frecuencia_valor: int | None = Field(default=None, gt=0, le=2_147_483_647)
    frecuencia_unidad: FrecuenciaUnidad | None = None
    hora_inicio: time | None = None
    estado: EstadoTratamiento | None = None
    medicamentos: list[TratamientoMedicamentoCreate] | None = None


class TratamientoResponse(BaseModel):
    id_tratamiento: int
    id_diagnostico: int
    descripcion: str
    medicamento_o_proceso: str | None = None
    dosis: str | None = None
    frecuencia: str | None = None
    fecha_inicio: date
    fecha_fin: date | None
    frecuencia_valor: int | None
    frecuencia_unidad: FrecuenciaUnidad | None
    hora_inicio: time | None
    estado: EstadoTratamiento
    medicamentos: list[TratamientoMedicamentoResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
