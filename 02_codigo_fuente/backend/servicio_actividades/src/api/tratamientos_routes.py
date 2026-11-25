from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database import get_db
from src.esquemas.actividad_schema import ActividadResponse
from src.logica_negocio.actividad_service import ActividadService
from src.logica_negocio.auth import verificar_token_access, veterinaria_o_manejo
from src.repositorios.actividad_repo import actividad_a_dict

router = APIRouter(
    prefix="/api/actividades/tratamientos",
    tags=["Tratamientos"],
    dependencies=[Depends(verificar_token_access)],
)


@router.post("/{id_tratamiento}/generar", response_model=List[ActividadResponse])
def generar_actividades_tratamiento(
    id_tratamiento: int,
    db: Session = Depends(get_db),
    usuario: dict = Depends(veterinaria_o_manejo),
):
    actividades = ActividadService.generar_tratamiento(
        db,
        id_tratamiento,
        usuario["id_usuario"],
    )
    return [actividad_a_dict(actividad) for actividad in actividades]


# Cualquier rol: la renovación del horizonte se dispara al abrir Planificación
@router.post("/renovar", response_model=List[ActividadResponse])
def renovar_horizonte_tratamientos(
    db: Session = Depends(get_db),
    usuario: dict = Depends(verificar_token_access),
):
    actividades = ActividadService.renovar_horizonte_tratamientos(
        db,
        usuario["id_usuario"],
    )
    return [actividad_a_dict(actividad) for actividad in actividades]
