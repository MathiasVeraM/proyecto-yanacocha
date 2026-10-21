from datetime import date
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

EstadoTratamiento = Literal["en_curso", "finalizado", "suspendido"]

# id_diagnostico viene en la ruta, por eso no se pide en el cuerpo
class TratamientoCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    medicamento_o_proceso: str = Field(min_length=1, max_length=200)
    dosis: Optional[str] = Field(None, max_length=100)
    frecuencia: Optional[str] = Field(None, max_length=100)
    # Si no se envía, se usa la fecha de hoy
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    estado: EstadoTratamiento = "en_curso"

class TratamientoUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    medicamento_o_proceso: Optional[str] = Field(None, min_length=1, max_length=200)
    dosis: Optional[str] = Field(None, max_length=100)
    frecuencia: Optional[str] = Field(None, max_length=100)
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    estado: Optional[EstadoTratamiento] = None

class TratamientoResponse(BaseModel):
    id_tratamiento: int
    id_diagnostico: int
    medicamento_o_proceso: str
    dosis: Optional[str]
    frecuencia: Optional[str]
    fecha_inicio: date
    fecha_fin: Optional[date]
    estado: str

    model_config = ConfigDict(from_attributes=True)
