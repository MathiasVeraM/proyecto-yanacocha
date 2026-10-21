from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from src.database import get_db
from src.esquemas.recinto_schema import RecintoCreate, RecintoResponse, RecintoUpdate
from src.logica_negocio.auth import verificar_acceso_modulo
from src.logica_negocio.recinto_service import RecintoService

router = APIRouter(
    prefix="/api/animales/recintos",
    tags=["Gestión Animal - Recintos"],
    dependencies=[Depends(verificar_acceso_modulo)],
)

@router.get("", response_model=List[RecintoResponse])
def listar_recintos(db: Session = Depends(get_db)):
    return RecintoService.listar_recintos(db)

@router.post("", response_model=RecintoResponse, status_code=status.HTTP_201_CREATED)
def crear_recinto(recinto_in: RecintoCreate, db: Session = Depends(get_db)):
    return RecintoService.crear_recinto(db, recinto_in)

@router.put("/{id_recinto}", response_model=RecintoResponse)
def actualizar_recinto(id_recinto: int, recinto_in: RecintoUpdate, db: Session = Depends(get_db)):
    return RecintoService.actualizar_recinto(db, id_recinto, recinto_in)
