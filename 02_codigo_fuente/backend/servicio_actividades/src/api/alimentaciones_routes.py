from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.esquemas.actividad_schema import ActividadResponse, AlimentacionCreate
from src.logica_negocio.actividad_service import ActividadService
from src.logica_negocio.auth import solo_manejo_animal, verificar_token_access
from src.repositorios.actividad_repo import actividad_a_dict

router = APIRouter(
    prefix="/api/actividades/alimentaciones",
    tags=["Alimentaciones"],
    dependencies=[Depends(verificar_token_access)],
)


@router.post("", response_model=ActividadResponse, status_code=status.HTTP_201_CREATED)
def programar_alimentacion(
    actividad_in: AlimentacionCreate,
    db: Session = Depends(get_db),
    usuario: dict = Depends(solo_manejo_animal),
    # true cuando la persona ya vio el aviso de cruce de horario y eligió "crear igual"
    permitir_cruce: bool = Query(False),
):
    actividad = ActividadService.crear(
        db,
        "alimentacion",
        actividad_in.model_dump(),
        usuario["id_usuario"],
        permitir_cruce,
    )
    return actividad_a_dict(actividad)
