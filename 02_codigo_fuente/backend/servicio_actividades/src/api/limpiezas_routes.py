from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.esquemas.actividad_schema import ActividadResponse
from src.esquemas.limpieza_schema import LimpiezaCreate
from src.logica_negocio.actividad_service import ActividadService
from src.logica_negocio.auth import verificar_token_access
from src.repositorios.actividad_repo import actividad_a_dict

router = APIRouter(
    prefix="/api/actividades/limpiezas",
    tags=["Limpiezas"],
    dependencies=[Depends(verificar_token_access)],
)


@router.post("", response_model=ActividadResponse, status_code=status.HTTP_201_CREATED)
def programar_limpieza(
    actividad_in: LimpiezaCreate,
    db: Session = Depends(get_db),
    usuario: dict = Depends(verificar_token_access),
):
    actividad = ActividadService.crear(
        db,
        "limpieza",
        actividad_in.model_dump(),
        usuario["id_usuario"],
    )
    return actividad_a_dict(actividad)
