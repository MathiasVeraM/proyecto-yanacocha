from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from src.database import get_db
from src.logica_negocio.salud_service import SaludService

# Sin autenticación y sin datos internos: solo los consultan Docker, el balanceador y el pipeline
router = APIRouter(prefix="/health", tags=["Salud"])


@router.get("")
def liveness():
    """El proceso está vivo y atiende peticiones; no consulta la base de datos."""
    return {"status": "ok"}


@router.get("/ready")
def readiness(db: Session = Depends(get_db)):
    """El servicio está listo para recibir tráfico: la base de datos responde."""
    if not SaludService.base_de_datos_disponible(db):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unavailable"},
        )
    return {"status": "ready"}
