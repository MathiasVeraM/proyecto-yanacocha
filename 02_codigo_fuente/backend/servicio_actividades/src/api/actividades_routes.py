from datetime import date
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.esquemas.actividad_schema import (
    ActividadBaseCreate,
    ActividadResponse,
    EventoCalendario,
)
from src.logica_negocio.actividad_service import ActividadService
from src.logica_negocio.auth import verificar_token_access
from src.repositorios.actividad_repo import actividad_a_dict

router = APIRouter(
    prefix="/api/actividades",
    tags=["Actividades"],
    dependencies=[Depends(verificar_token_access)],
)


@router.get("", response_model=List[ActividadResponse])
def listar_actividades(
    id_animal: int | None = None,
    id_recinto: int | None = None,
    tipo_actividad: str | None = None,
    completada: bool | None = None,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    db: Session = Depends(get_db),
):
    actividades = ActividadService.listar(
        db,
        id_animal,
        id_recinto,
        tipo_actividad,
        completada,
        fecha_desde,
        fecha_hasta,
    )
    return [actividad_a_dict(actividad) for actividad in actividades]


@router.get("/calendario", response_model=List[EventoCalendario])
def consultar_calendario(
    id_animal: int | None = None,
    id_recinto: int | None = None,
    tipo_actividad: str | None = None,
    completada: bool | None = None,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    db: Session = Depends(get_db),
):
    actividades = ActividadService.listar(
        db,
        id_animal,
        id_recinto,
        tipo_actividad,
        completada,
        fecha_desde,
        fecha_hasta,
    )
    return ActividadService.calendario(actividades)


@router.post("", response_model=ActividadResponse, status_code=status.HTTP_201_CREATED)
def programar_actividad(
    actividad_in: ActividadBaseCreate,
    db: Session = Depends(get_db),
    usuario: dict = Depends(verificar_token_access),
):
    actividad = ActividadService.crear_desde_esquema(
        db,
        actividad_in,
        usuario["id_usuario"],
    )
    return actividad_a_dict(actividad)


@router.get("/{id_actividad}", response_model=ActividadResponse)
def obtener_actividad(id_actividad: int, db: Session = Depends(get_db)):
    actividad = ActividadService.actividad_o_404(db, id_actividad)
    return actividad_a_dict(actividad)
