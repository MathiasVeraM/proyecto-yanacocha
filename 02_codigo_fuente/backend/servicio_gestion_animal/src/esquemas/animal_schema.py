from datetime import date
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field
from src.esquemas.recinto_schema import RecintoResponse
from src.esquemas.taxonomia_schema import TaxonomiaResponse

EstadoAnimal = Literal["en_centro", "en_tratamiento", "liberado", "trasladado", "fallecido"]
Sexo = Literal["macho", "hembra", "indeterminado"]

# El código no se envía: lo genera el servicio a partir del nombre científico
class AnimalCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    id_taxonomia: int
    id_recinto: int
    edad_aproximada: Optional[str] = Field(None, max_length=50)
    sexo: Optional[Sexo] = None
    estado_actual: EstadoAnimal = "en_centro"
    # Si no se envía, se usa la fecha de hoy
    fecha_ingreso: Optional[date] = None
    url_imagen: Optional[str] = Field(None, max_length=500)

# El código y la especie no se editan: el código depende del nombre científico
class AnimalUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    id_recinto: Optional[int] = None
    edad_aproximada: Optional[str] = Field(None, max_length=50)
    sexo: Optional[Sexo] = None
    estado_actual: Optional[EstadoAnimal] = None
    fecha_ingreso: Optional[date] = None
    url_imagen: Optional[str] = Field(None, max_length=500)

class AnimalResponse(BaseModel):
    id_animal: int
    codigo_animal: str
    id_taxonomia: int
    id_recinto: int
    edad_aproximada: Optional[str]
    sexo: Optional[str]
    estado_actual: str
    fecha_ingreso: date
    url_imagen: Optional[str]
    taxonomia: TaxonomiaResponse
    recinto: RecintoResponse

    model_config = ConfigDict(from_attributes=True)
