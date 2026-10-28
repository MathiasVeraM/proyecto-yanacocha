from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from src.esquemas.signos_vitales_schema import SignosVitalesCreate, SignosVitalesResponse

# id_animal viene en la ruta e id_usuario en el token, por eso no se piden en el cuerpo
class DiagnosticoCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    diagnostico: str = Field(min_length=1)
    observaciones: Optional[str] = None
    es_critico: bool = False
    signos_vitales: Optional[SignosVitalesCreate] = None

# No se permite cambiar el animal ni el usuario que registró el diagnóstico
class DiagnosticoUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    diagnostico: Optional[str] = Field(None, min_length=1)
    observaciones: Optional[str] = None
    es_critico: Optional[bool] = None
    signos_vitales: Optional[SignosVitalesCreate] = None

class DiagnosticoResponse(BaseModel):
    id_diagnostico: int
    id_animal: int
    id_usuario: int
    diagnostico: str
    observaciones: Optional[str]
    es_critico: bool
    fecha_registro: datetime
    signos_vitales: Optional[SignosVitalesResponse] = None

    model_config = ConfigDict(from_attributes=True)
