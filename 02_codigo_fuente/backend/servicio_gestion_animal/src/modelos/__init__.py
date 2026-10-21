# Registramos todos los modelos en el metadata de SQLAlchemy, porque diagnostico depende de animal
# y tratamiento de diagnostico (ForeignKey)
from src.modelos.animal_model import AnimalModel, DiagnosticoModel, TratamientoModel

__all__ = ["AnimalModel", "DiagnosticoModel", "TratamientoModel"]
