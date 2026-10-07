from typing import Optional
from pydantic import BaseModel

class RolCreate(BaseModel):
    nombre_rol: str
    descripcion: Optional[str] = None

class ModuloCreate(BaseModel):
    nombre_modulo: str
    codigo_servicio: str