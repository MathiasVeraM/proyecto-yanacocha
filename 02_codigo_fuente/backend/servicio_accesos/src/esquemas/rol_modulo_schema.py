from typing import Optional
from pydantic import BaseModel, Field

class RolCreate(BaseModel):
    nombre_rol: str
    descripcion: Optional[str] = None

class ModuloCreate(BaseModel):
    nombre_modulo: str
    codigo_servicio: str


class RolUpdate(BaseModel):
    nombre_rol: Optional[str] = Field(None, min_length=1, max_length=50)
    descripcion: Optional[str] = None


class ModuloUpdate(BaseModel):
    nombre_modulo: Optional[str] = Field(None, min_length=1, max_length=100)
    codigo_servicio: Optional[str] = Field(None, min_length=1, max_length=50)
