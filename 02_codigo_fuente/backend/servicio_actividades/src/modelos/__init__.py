from src.modelos import referencias_model as referencias_model
from src.modelos.actividad_model import ActividadModel
from src.modelos.actividad_alimentacion_model import ActividadAlimentacionModel
from src.modelos.actividad_enriquecimiento_model import ActividadEnriquecimientoModel
from src.modelos.actividad_entrenamiento_model import ActividadEntrenamientoModel
from src.modelos.actividad_tratamiento_model import ActividadTratamientoModel
from src.modelos.dieta_model import DietaModel
from src.modelos.dieta_alimento_model import DietaAlimentoModel
from src.modelos.observacion_actividad_model import ObservacionActividadModel

__all__ = [
    "ActividadModel",
    "ActividadAlimentacionModel",
    "ActividadEnriquecimientoModel",
    "ActividadEntrenamientoModel",
    "ActividadTratamientoModel",
    "DietaModel",
    "DietaAlimentoModel",
    "ObservacionActividadModel",
    "referencias_model",
]
