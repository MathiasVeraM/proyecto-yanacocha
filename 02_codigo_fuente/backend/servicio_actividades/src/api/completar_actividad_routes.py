from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database import get_db
from src.esquemas.actividad_schema import ActividadResponse, CompletarActividad
from src.logica_negocio.actividad_service import ActividadService
from src.logica_negocio.auth import verificar_token_access
from src.repositorios.actividad_repo import actividad_a_dict

router = APIRouter(
    prefix="/api/actividades",
    tags=["Completar actividad"],
    dependencies=[Depends(verificar_token_access)],
)


@router.post("/{id_actividad}/completar", response_model=ActividadResponse)
@router.patch("/{id_actividad}/completar", response_model=ActividadResponse)
def completar_actividad(
    id_actividad: int,
    datos: CompletarActividad,
    db: Session = Depends(get_db),
    usuario: dict = Depends(verificar_token_access),
):
    actividad = ActividadService.completar(
        db,
        id_actividad,
        usuario["id_usuario"],
        datos.observaciones,
        "observaciones" in datos.model_fields_set,
    )
    resultado = actividad_a_dict(actividad)
    resultado["id_actividad"] = actividad.id_actividad
    return resultado


@router.post("/{id_actividad}/reabrir", response_model=ActividadResponse)
def reabrir_actividad(id_actividad: int, db: Session = Depends(get_db)):
    actividad = ActividadService.reabrir(db, id_actividad)
    return actividad_a_dict(actividad)
