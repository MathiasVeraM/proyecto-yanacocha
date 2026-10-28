# Import all models so SQLAlchemy registers their tables and resolves string foreign keys.
from src.modelos.animal_model import AnimalImagenModel, AnimalModel, RecintoModel, TaxonomiaModel
from src.modelos.diagnostico_model import DiagnosticoModel
from src.modelos.signos_vitales_model import SignosVitalesModel
from src.modelos.tratamiento_model import TratamientoModel

__all__ = [
    "AnimalImagenModel", "AnimalModel", "DiagnosticoModel", "RecintoModel", "SignosVitalesModel",
    "TaxonomiaModel", "TratamientoModel"
]
