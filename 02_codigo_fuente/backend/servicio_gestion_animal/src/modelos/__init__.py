# Registramos todos los modelos en el metadata de SQLAlchemy, porque animal depende de taxonomia y recinto,
# animal_imagen y diagnostico de animal, y tratamiento de diagnostico (ForeignKey)
from src.modelos.animal_model import (
    AnimalImagenModel, AnimalModel, DiagnosticoModel, RecintoModel, TaxonomiaModel, TratamientoModel
)

__all__ = [
    "AnimalImagenModel", "AnimalModel", "DiagnosticoModel", "RecintoModel", "TaxonomiaModel", "TratamientoModel"
]
