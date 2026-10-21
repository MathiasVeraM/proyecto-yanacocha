from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

class TaxonomiaCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nombre_comun: str = Field(min_length=1, max_length=100)
    especie: str = Field(min_length=1, max_length=150)
    genero: Optional[str] = Field(None, max_length=100)
    familia: Optional[str] = Field(None, max_length=100)
    orden: Optional[str] = Field(None, max_length=100)
    clase: Optional[str] = Field(None, max_length=100)

class TaxonomiaUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nombre_comun: Optional[str] = Field(None, min_length=1, max_length=100)
    especie: Optional[str] = Field(None, min_length=1, max_length=150)
    genero: Optional[str] = Field(None, max_length=100)
    familia: Optional[str] = Field(None, max_length=100)
    orden: Optional[str] = Field(None, max_length=100)
    clase: Optional[str] = Field(None, max_length=100)

class TaxonomiaResponse(BaseModel):
    id_taxonomia: int
    nombre_comun: str
    especie: str
    genero: Optional[str]
    familia: Optional[str]
    orden: Optional[str]
    clase: Optional[str]
    id_inaturalist: Optional[int]

    model_config = ConfigDict(from_attributes=True)

class TaxonomiaImportar(BaseModel):
    id_inaturalist: int = Field(gt=0)

class SugerenciaTaxonomia(BaseModel):
    # catalogo: ya está guardada y se usa su id_taxonomia
    # inaturalist: hay que importarla antes de usarla, con su id_inaturalist
    origen: Literal["catalogo", "inaturalist"]
    id_taxonomia: Optional[int] = None
    id_inaturalist: Optional[int] = None
    nombre_comun: Optional[str] = None
    especie: str
