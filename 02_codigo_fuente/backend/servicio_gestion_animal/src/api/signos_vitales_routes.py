from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database import get_db
from src.esquemas.signos_vitales_schema import SignosVitalesHistorialResponse
from src.logica_negocio.auth import verificar_acceso_modulo
from src.logica_negocio.signos_vitales_service import SignosVitalesService

router = APIRouter(
    prefix="/api/animales",
    tags=["Signos vitales"],
    dependencies=[Depends(verificar_acceso_modulo)],
)


@router.get(
    "/{id_animal}/signos-vitales",
    response_model=List[SignosVitalesHistorialResponse],
)
def listar_signos_vitales(id_animal: int, db: Session = Depends(get_db)):
    return SignosVitalesService.listar_por_animal(db, id_animal)
