from pydantic import BaseModel


# Solo lo que Planificación necesita para mostrar nombres y llenar sus selectores: sin fotos,
# datos clínicos, correos ni roles.

class TaxonomiaReferencia(BaseModel):
    id_taxonomia: int
    nombre_comun: str
    especie: str
    clase: str | None = None


class RecintoReferencia(BaseModel):
    id_recinto: int
    nombre_recinto: str
    tipo: str | None = None
    capacidad: int | None = None
    estado: str


class AnimalReferencia(BaseModel):
    id_animal: int
    codigo_animal: str
    nombre: str | None = None
    id_taxonomia: int
    id_recinto: int
    estado_actual: str
    taxonomia: TaxonomiaReferencia
    recinto: RecintoReferencia


class UsuarioReferencia(BaseModel):
    id_usuario: int
    nombre: str
    apellido: str
    # Los inactivos se incluyen para mostrar quién programó actividades antiguas
    activo: bool


class ReferenciasPlanificacion(BaseModel):
    animales: list[AnimalReferencia]
    recintos: list[RecintoReferencia]
    usuarios: list[UsuarioReferencia]
