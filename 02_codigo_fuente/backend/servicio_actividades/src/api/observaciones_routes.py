from datetime import date
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.esquemas.observacion_schema import ObservacionCreate, ObservacionResponse
from src.logica_negocio.auth import manejo_o_voluntario, verificar_token_access
from src.logica_negocio.observacion_service import ObservacionService

router = APIRouter(
    prefix="/api/actividades",
    tags=["Observaciones de actividades"],
    dependencies=[Depends(verificar_token_access)],
)


# Este router se incluye antes que el de actividades en src/main.py para que
# /observaciones no sea capturado por GET /api/actividades/{id_actividad}.
@router.get("/observaciones", response_model=List[ObservacionResponse])
def listar_observaciones(
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    db: Session = Depends(get_db),
):
    return ObservacionService.listar_por_fechas(db, fecha_desde, fecha_hasta)


@router.post(
    "/{id_actividad}/observaciones",
    response_model=ObservacionResponse,
    status_code=status.HTTP_201_CREATED,
)
def registrar_observacion(
    id_actividad: int,
    observacion_in: ObservacionCreate,
    db: Session = Depends(get_db),
    usuario: dict = Depends(manejo_o_voluntario),
):
    return ObservacionService.crear(
        db,
        id_actividad,
        observacion_in,
        usuario["id_usuario"],
    )


@router.get("/{id_actividad}/observaciones", response_model=List[ObservacionResponse])
def listar_observaciones_actividad(id_actividad: int, db: Session = Depends(get_db)):
    return ObservacionService.listar_por_actividad(db, id_actividad)
