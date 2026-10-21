from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

EstadoRecinto = Literal["disponible", "en_limpieza", "en_mantenimiento"]

class RecintoCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nombre_recinto: str = Field(min_length=1, max_length=100)
    tipo: Optional[str] = Field(None, max_length=50)
    capacidad: Optional[int] = Field(None, gt=0)
    estado: EstadoRecinto = "disponible"

class RecintoUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nombre_recinto: Optional[str] = Field(None, min_length=1, max_length=100)
    tipo: Optional[str] = Field(None, max_length=50)
    capacidad: Optional[int] = Field(None, gt=0)
    estado: Optional[EstadoRecinto] = None

class RecintoResponse(BaseModel):
    id_recinto: int
    nombre_recinto: str
    tipo: Optional[str]
    capacidad: Optional[int]
    estado: str

    model_config = ConfigDict(from_attributes=True)
