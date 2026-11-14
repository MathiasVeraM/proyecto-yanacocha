from datetime import date
from typing import Any, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from src.esquemas.recinto_schema import RecintoResponse
from src.modelos.fechas import hoy_local
from src.esquemas.taxonomia_schema import TaxonomiaResponse

EstadoAnimal = Literal["en_centro", "en_tratamiento", "liberado", "trasladado", "fallecido"]
Sexo = Literal["macho", "hembra", "indeterminado"]

def _validar_ingreso(fecha: Optional[date]) -> Optional[date]:
    if fecha is not None and fecha > hoy_local():
        raise ValueError("La fecha de ingreso no puede ser futura")
    return fecha


# El código no se envía: lo genera el servicio con el formato YC-año-número.
# La foto se sube aparte (PUT /api/animales/{id}/imagen) y el servicio llena url_imagen
class AnimalCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    id_taxonomia: int
    id_recinto: int
    # Nombre propio del ejemplar (ej. "Yaku"); el nombre común es de la especie
    nombre: Optional[str] = Field(None, max_length=100)
    edad_anios: int = Field(ge=0, le=200)
    edad_meses: int = Field(ge=0, le=11)
    sexo: Optional[Sexo] = None
    estado_actual: EstadoAnimal = "en_centro"
    # Si no se envía, se usa la fecha de hoy
    fecha_ingreso: Optional[date] = None

    @field_validator("fecha_ingreso")
    @classmethod
    def ingreso_no_futuro(cls, fecha: Optional[date]) -> Optional[date]:
        return _validar_ingreso(fecha)

    @model_validator(mode="before")
    @classmethod
    def validar_y_completar_edad(cls, valores: Any) -> Any:
        if not isinstance(valores, dict):
            return valores
        datos = valores.copy()
        anios = datos.get("edad_anios")
        meses = datos.get("edad_meses")
        if anios is None and meses is None:
            raise ValueError("Ingresa la edad en años o meses.")
        datos.setdefault("edad_anios", 0)
        datos.setdefault("edad_meses", 0)
        if datos["edad_anios"] is None:
            datos["edad_anios"] = 0
        if datos["edad_meses"] is None:
            datos["edad_meses"] = 0
        return datos

# El código se conserva al editar; la taxonomía puede corregirse seleccionando otra del catálogo
class AnimalUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    id_taxonomia: Optional[int] = None
    id_recinto: Optional[int] = None
    nombre: Optional[str] = Field(None, max_length=100)
    edad_anios: Optional[int] = Field(None, ge=0, le=200)
    edad_meses: Optional[int] = Field(None, ge=0, le=11)
    sexo: Optional[Sexo] = None
    estado_actual: Optional[EstadoAnimal] = None
    fecha_ingreso: Optional[date] = None

    @field_validator("fecha_ingreso")
    @classmethod
    def ingreso_no_futuro(cls, fecha: Optional[date]) -> Optional[date]:
        return _validar_ingreso(fecha)

    @model_validator(mode="before")
    @classmethod
    def completar_edad_parcial(cls, valores: Any) -> Any:
        if not isinstance(valores, dict):
            return valores
        datos = valores.copy()
        campos_edad = {"edad_anios", "edad_meses"}
        if not campos_edad.intersection(datos):
            return datos
        anios = datos.get("edad_anios")
        meses = datos.get("edad_meses")
        if anios is None and meses is None:
            raise ValueError("Ingresa la edad en años o meses.")
        if anios is None:
            datos["edad_anios"] = 0
        if meses is None:
            datos["edad_meses"] = 0
        return datos

class AnimalResponse(BaseModel):
    id_animal: int
    codigo_animal: str
    nombre: Optional[str] = None
    id_taxonomia: int
    id_recinto: int
    edad_anios: Optional[int] = None
    edad_meses: Optional[int] = None
    edad_aproximada: Optional[str] = None
    sexo: Optional[str] = None
    estado_actual: str
    fecha_ingreso: date
    url_imagen: Optional[str] = None
    taxonomia: TaxonomiaResponse
    recinto: RecintoResponse
    # Alerta para las tarjetas del listado; se calcula en la misma consulta del animal
    tiene_tratamiento_en_curso: bool = False

    model_config = ConfigDict(from_attributes=True)
