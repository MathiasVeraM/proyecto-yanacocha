from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database import get_db
from src.esquemas.actividad_schema import ActividadResponse
from src.esquemas.tomas_alimentacion_schema import GenerarTomas
from src.logica_negocio.actividad_service import ActividadService
from src.logica_negocio.auth import solo_manejo_animal, verificar_token_access
from src.repositorios.actividad_repo import actividad_a_dict

router = APIRouter(
    prefix="/api/actividades/tomas",
    tags=["Tomas de alimentación"],
    dependencies=[Depends(verificar_token_access)],
)


@router.post("/generar")
def generar_tomas(
    solicitud: GenerarTomas,
    db: Session = Depends(get_db),
    usuario: dict = Depends(solo_manejo_animal),
):
    tomas = ActividadService.generar_tomas(
        db,
        solicitud.id_dieta,
        usuario["id_usuario"],
        solicitud.fecha_hasta,
    )
    resultado = []
    for toma in tomas:
        datos = actividad_a_dict(toma)
        datos["id_actividad"] = toma.id_actividad
        resultado.append(datos)
    return {"tomas": resultado}


# Cualquier rol: la renovación del horizonte se dispara al abrir Planificación
@router.post("/renovar", response_model=List[ActividadResponse])
def renovar_horizonte(
    db: Session = Depends(get_db),
    usuario: dict = Depends(verificar_token_access),
):
    tomas = ActividadService.renovar_horizonte(db, usuario["id_usuario"])
    return [actividad_a_dict(toma) for toma in tomas]
