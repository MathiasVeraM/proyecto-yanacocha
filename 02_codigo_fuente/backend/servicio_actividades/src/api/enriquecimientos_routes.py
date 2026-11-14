from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.esquemas.actividad_schema import ActividadResponse
from src.esquemas.enriquecimiento_schema import EnriquecimientoCreate
from src.logica_negocio.actividad_service import ActividadService
from src.logica_negocio.auth import solo_manejo_animal, verificar_token_access
from src.repositorios.actividad_repo import actividad_a_dict
from src.repositorios.referencias_repo import ReferenciasRepository


router = APIRouter(
    prefix="/api/actividades/enriquecimientos",
    tags=["Enriquecimientos"],
    dependencies=[Depends(verificar_token_access)],
)


@router.post("", response_model=ActividadResponse, status_code=status.HTTP_201_CREATED)
def programar_enriquecimiento(
    actividad_in: EnriquecimientoCreate,
    db: Session = Depends(get_db),
    usuario: dict = Depends(solo_manejo_animal),
    # true cuando la persona ya vio el aviso de cruce de horario y eligió "crear igual"
    permitir_cruce: bool = Query(False),
):
    actividad = ActividadService.crear(
        db,
        "enriquecimiento",
        actividad_in.model_dump(),
        usuario["id_usuario"],
        permitir_cruce,
    )
    return actividad_a_dict(actividad)


@router.get("", response_model=List[ActividadResponse])
def listar_enriquecimientos(
    id_animal: int | None = None,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    db: Session = Depends(get_db),
):
    if id_animal is not None and not ReferenciasRepository.existe_animal(db, id_animal):
        raise HTTPException(status_code=404, detail="Animal no encontrado")
    actividades = ActividadService.listar(
        db,
        id_animal=id_animal,
        tipo_actividad="enriquecimiento",
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )
    return [actividad_a_dict(actividad) for actividad in actividades]
