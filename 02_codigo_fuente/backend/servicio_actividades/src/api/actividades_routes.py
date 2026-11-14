from datetime import date
from typing import List

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.esquemas.actividad_schema import (
    ActividadBaseCreate,
    ActividadRepetidaCreate,
    ActividadResponse,
    ActividadUpdate,
    EventoCalendario,
    LimitesActividades,
)
from src.logica_negocio import reglas_actividad
from src.logica_negocio.actividad_service import ActividadService
from src.logica_negocio.auth import solo_manejo_animal, verificar_token_access
from src.repositorios.actividad_repo import actividad_a_dict

router = APIRouter(
    prefix="/api/actividades",
    tags=["Actividades"],
    dependencies=[Depends(verificar_token_access)],
)


# Límites de fechas y duración, para usarlos como min y max en los formularios
@router.get("/limites", response_model=LimitesActividades)
def consultar_limites():
    return reglas_actividad.limites()


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
    usuario: dict = Depends(solo_manejo_animal),
    permitir_cruce: bool = Query(False),
):
    actividad = ActividadService.crear_desde_esquema(
        db,
        actividad_in,
        usuario["id_usuario"],
        permitir_cruce,
    )
    return actividad_a_dict(actividad)


@router.post("/repetidas", response_model=List[ActividadResponse], status_code=status.HTTP_201_CREATED)
def programar_actividad_repetida(
    actividad_in: ActividadRepetidaCreate,
    db: Session = Depends(get_db),
    usuario: dict = Depends(solo_manejo_animal),
    permitir_cruce: bool = Query(False),
):
    # La misma actividad todos los días o ciertos días, hasta una fecha o durante N meses
    datos = actividad_in.model_dump(exclude={"tipo_actividad", "repeticion"}, exclude_none=True)
    actividades = ActividadService.crear_repetida(
        db,
        actividad_in.tipo_actividad,
        datos,
        actividad_in.repeticion.model_dump(),
        usuario["id_usuario"],
        permitir_cruce,
    )
    return [actividad_a_dict(actividad) for actividad in actividades]


@router.put(
    "/{id_actividad}",
    response_model=ActividadResponse,
    dependencies=[Depends(solo_manejo_animal)],
)
def editar_actividad(
    id_actividad: int,
    cambios: ActividadUpdate,
    db: Session = Depends(get_db),
    permitir_cruce: bool = Query(False),
):
    actividad = ActividadService.actualizar(
        db, id_actividad, cambios.model_dump(exclude_unset=True), permitir_cruce
    )
    return actividad_a_dict(actividad)


@router.delete(
    "/{id_actividad}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(solo_manejo_animal)],
)
def eliminar_actividad(id_actividad: int, db: Session = Depends(get_db)):
    ActividadService.eliminar(db, id_actividad)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{id_actividad}", response_model=ActividadResponse)
def obtener_actividad(id_actividad: int, db: Session = Depends(get_db)):
    actividad = ActividadService.actividad_o_404(db, id_actividad)
    return actividad_a_dict(actividad)
