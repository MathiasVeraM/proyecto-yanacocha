from datetime import date
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

EstadoAnimal = Literal["en_centro", "en_tratamiento", "liberado", "trasladado", "fallecido"]
Sexo = Literal["macho", "hembra", "indeterminado"]

class AnimalCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    codigo_animal: str = Field(min_length=1, max_length=30)
    nombre_comun: str = Field(min_length=1, max_length=100)
    especie: Optional[str] = Field(None, max_length=150)
    genero: Optional[str] = Field(None, max_length=100)
    familia: Optional[str] = Field(None, max_length=100)
    edad_aproximada: Optional[str] = Field(None, max_length=50)
    sexo: Optional[Sexo] = None
    estado_actual: EstadoAnimal = "en_centro"
    # Si no se envía, se usa la fecha de hoy
    fecha_ingreso: Optional[date] = None
    url_imagen: Optional[str] = Field(None, max_length=500)

class AnimalUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    codigo_animal: Optional[str] = Field(None, min_length=1, max_length=30)
    nombre_comun: Optional[str] = Field(None, min_length=1, max_length=100)
    especie: Optional[str] = Field(None, max_length=150)
    genero: Optional[str] = Field(None, max_length=100)
    familia: Optional[str] = Field(None, max_length=100)
    edad_aproximada: Optional[str] = Field(None, max_length=50)
    sexo: Optional[Sexo] = None
    estado_actual: Optional[EstadoAnimal] = None
    fecha_ingreso: Optional[date] = None
    url_imagen: Optional[str] = Field(None, max_length=500)

class AnimalResponse(BaseModel):
    id_animal: int
    codigo_animal: str
    nombre_comun: str
    especie: Optional[str]
    genero: Optional[str]
    familia: Optional[str]
    edad_aproximada: Optional[str]
    sexo: Optional[str]
    estado_actual: str
    fecha_ingreso: date
    url_imagen: Optional[str]

    model_config = ConfigDict(from_attributes=True)
