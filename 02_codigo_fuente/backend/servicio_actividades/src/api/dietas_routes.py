from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.esquemas.dieta_schema import DietaCreate, DietaResponse
from src.logica_negocio.auth import verificar_token_access
from src.logica_negocio.dieta_service import DietaService

router = APIRouter(
    prefix="/api/actividades",
    tags=["Dietas"],
    dependencies=[Depends(verificar_token_access)],
)


@router.post(
    "/dietas",
    response_model=DietaResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_dieta(
    dieta_in: DietaCreate,
    db: Session = Depends(get_db),
    usuario: dict = Depends(verificar_token_access),
):
    return DietaService.crear_dieta(db, usuario["id_usuario"], dieta_in)


@router.get("/dietas", response_model=List[DietaResponse])
def listar_todas_las_dietas(db: Session = Depends(get_db)):
    # Historial de dietas de todos los animales en una sola petición (Planificación),
    # en lugar de una petición por animal
    return DietaService.listar_todas(db)


@router.get(
    "/animales/{id_animal}/dietas",
    response_model=List[DietaResponse],
)
def listar_dietas(id_animal: int, db: Session = Depends(get_db)):
    return DietaService.listar_por_animal(db, id_animal)


@router.get(
    "/animales/{id_animal}/dietas/vigente",
    response_model=DietaResponse,
)
def obtener_dieta_vigente(id_animal: int, db: Session = Depends(get_db)):
    return DietaService.vigente_por_animal(db, id_animal)


@router.get("/dietas/{id_dieta}", response_model=DietaResponse)
def obtener_dieta(id_dieta: int, db: Session = Depends(get_db)):
    return DietaService.dieta_o_404(db, id_dieta)
