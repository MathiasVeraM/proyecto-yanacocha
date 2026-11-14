from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database import get_db
from src.esquemas.referencias_schema import ReferenciasPlanificacion
from src.logica_negocio.auth import verificar_token_access
from src.logica_negocio.referencias_service import ReferenciasService

router = APIRouter(
    prefix="/api/actividades",
    tags=["Referencias de planificación"],
    dependencies=[Depends(verificar_token_access)],
)


# Este router se incluye antes que el de actividades en src/main.py para que
# /referencias no sea capturado por GET /api/actividades/{id_actividad}.
@router.get("/referencias", response_model=ReferenciasPlanificacion)
def consultar_referencias(db: Annotated[Session, Depends(get_db)]):
    # Todos los roles con el módulo de Planificación pueden consultarlas: así no necesitan
    # permisos sobre Fichas ni Accesos solo para ver nombres de ejemplares, recintos y usuarios
    return ReferenciasService.planificacion(db)
