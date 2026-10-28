from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer, model_validator

Hidratacion = Literal[
    "normal",
    "deshidratacion_leve",
    "deshidratacion_moderada",
    "deshidratacion_severa",
]
Mucosas = Literal["rosadas", "palidas", "cianoticas", "ictericas", "congestionadas"]
Actitud = Literal["alerta", "deprimido", "estuporoso", "agitado"]
_CAMPOS_SIGNOS_VITALES = (
    "peso_kg",
    "temperatura_c",
    "frecuencia_cardiaca_lpm",
    "frecuencia_respiratoria_rpm",
    "tiempo_llenado_capilar_s",
    "hidratacion",
    "condicion_corporal",
    "mucosas",
    "actitud",
)


class SignosVitalesCampos(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    peso_kg: Decimal | None = Field(None, gt=0, max_digits=8, decimal_places=3)
    temperatura_c: Decimal | None = Field(None, ge=0, le=60, max_digits=4, decimal_places=1)
    frecuencia_cardiaca_lpm: int | None = Field(None, gt=0)
    frecuencia_respiratoria_rpm: int | None = Field(None, gt=0)
    tiempo_llenado_capilar_s: Decimal | None = Field(None, gt=0, max_digits=4, decimal_places=1)
    hidratacion: Hidratacion | None = None
    condicion_corporal: int | None = Field(None, ge=1, le=5)
    mucosas: Mucosas | None = None
    actitud: Actitud | None = None

    @model_validator(mode="after")
    def debe_incluir_al_menos_un_signo(self):
        if all(getattr(self, campo) is None for campo in _CAMPOS_SIGNOS_VITALES):
            raise ValueError("Debe proporcionarse al menos un signo vital")
        return self


class SignosVitalesCreate(SignosVitalesCampos):
    pass


class SignosVitalesResponse(SignosVitalesCampos):
    id_signos_vitales: int
    id_diagnostico: int

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("peso_kg", "temperatura_c", "tiempo_llenado_capilar_s", when_used="json")
    def serializar_decimal(self, valor: Decimal | None) -> float | None:
        return float(valor) if valor is not None else None


class SignosVitalesHistorialResponse(SignosVitalesResponse):
    fecha_diagnostico: datetime
