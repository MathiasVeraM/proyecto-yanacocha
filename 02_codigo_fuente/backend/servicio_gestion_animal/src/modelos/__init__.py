# Registramos todos los modelos en el metadata de SQLAlchemy, porque animal depende de taxonomia y recinto,
# diagnostico de animal y tratamiento de diagnostico (ForeignKey)
from src.modelos.animal_model import (
    AnimalModel, DiagnosticoModel, RecintoModel, TaxonomiaModel, TratamientoModel
)

__all__ = ["AnimalModel", "DiagnosticoModel", "RecintoModel", "TaxonomiaModel", "TratamientoModel"]
