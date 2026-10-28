from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.esquemas.tratamiento_schema import TratamientoCreate, TratamientoResponse, TratamientoUpdate
from src.logica_negocio.auth import verificar_acceso_modulo
from src.logica_negocio.tratamiento_service import TratamientoService

router = APIRouter(
    prefix="/api/animales",
    tags=["Tratamientos Veterinarios"],
    dependencies=[Depends(verificar_acceso_modulo)],
)


@router.get("/diagnosticos/{id_diagnostico}/tratamientos", response_model=List[TratamientoResponse])
def listar_tratamientos(id_diagnostico: int, db: Session = Depends(get_db)):
    return TratamientoService.listar_por_diagnostico(db, id_diagnostico)


@router.post(
    "/diagnosticos/{id_diagnostico}/tratamientos",
    response_model=TratamientoResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_tratamiento(
    id_diagnostico: int,
    tratamiento_in: TratamientoCreate,
    db: Session = Depends(get_db),
):
    return TratamientoService.crear_tratamiento(db, id_diagnostico, tratamiento_in)


@router.put("/tratamientos/{id_tratamiento}", response_model=TratamientoResponse)
def actualizar_tratamiento(
    id_tratamiento: int,
    tratamiento_in: TratamientoUpdate,
    db: Session = Depends(get_db),
):
    return TratamientoService.actualizar_tratamiento(db, id_tratamiento, tratamiento_in)
