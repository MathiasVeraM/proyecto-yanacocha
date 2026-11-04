from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer, model_validator

from src.config import ZONA_HORARIA


def _hoy_local() -> date:
    return datetime.now(ZONA_HORARIA).date()


UnidadFrecuencia = Literal["horas", "dias", "semanas"]


class DietaAlimentoCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nombre_alimento: str = Field(min_length=1, max_length=150)
    cantidad_gramos: Decimal = Field(gt=0, max_digits=8, decimal_places=2)


class DietaAlimentoResponse(BaseModel):
    id_dieta_alimento: int
    id_dieta: int
    nombre_alimento: str
    cantidad_gramos: Decimal

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("cantidad_gramos")
    def serializar_cantidad_gramos(self, cantidad: Decimal) -> float:
        return float(cantidad)


class DietaCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    id_animal: int = Field(gt=0)
    fecha_inicio: date
    fecha_fin: date | None = None
    frecuencia_valor: int = Field(gt=0, le=2147483647)
    frecuencia_unidad: UnidadFrecuencia
    alimentos: list[DietaAlimentoCreate] = Field(min_length=1)
    observaciones: str | None = None

    @model_validator(mode="after")
    def validar_fechas(self):
        if self.fecha_fin is not None and self.fecha_fin < self.fecha_inicio:
            raise ValueError("fecha_fin debe ser igual o posterior a fecha_inicio")
        return self


class DietaResponse(BaseModel):
    id_dieta: int
    id_animal: int
    id_usuario_creador: int
    fecha_inicio: date = Field(default_factory=_hoy_local)
    fecha_fin: date | None
    frecuencia_valor: int
    frecuencia_unidad: str
    vigente: bool
    observaciones: str | None
    fecha_registro: datetime
    alimentos: list[DietaAlimentoResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
