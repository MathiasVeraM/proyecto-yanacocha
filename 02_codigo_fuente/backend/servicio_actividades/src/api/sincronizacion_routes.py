from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database import get_db
from src.esquemas.sincronizacion_schema import SincronizacionRequest, SincronizacionResponse
from src.logica_negocio.auth import manejo_o_voluntario, verificar_token_access
from src.logica_negocio.sincronizacion_service import SincronizacionService

router = APIRouter(
    prefix="/api/actividades",
    tags=["Sincronización offline"],
    dependencies=[Depends(verificar_token_access)],
)


@router.post("/sincronizar", response_model=SincronizacionResponse)
def sincronizar(
    datos: SincronizacionRequest,
    db: Session = Depends(get_db),
    usuario: dict = Depends(manejo_o_voluntario),
):
    """Sube de una vez lo completado y observado sin conexión (idempotente, resultado por registro)."""
    return SincronizacionService.sincronizar(db, datos, usuario["id_usuario"])
