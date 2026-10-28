from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.esquemas.diagnostico_schema import DiagnosticoCreate, DiagnosticoResponse, DiagnosticoUpdate
from src.logica_negocio.auth import verificar_acceso_modulo
from src.logica_negocio.diagnostico_service import DiagnosticoService

router = APIRouter(
    prefix="/api/animales",
    tags=["Diagnósticos Veterinarios"],
    dependencies=[Depends(verificar_acceso_modulo)],
)


@router.get("/{id_animal}/diagnosticos", response_model=List[DiagnosticoResponse])
def listar_diagnosticos(id_animal: int, db: Session = Depends(get_db)):
    return DiagnosticoService.listar_por_animal(db, id_animal)


@router.post(
    "/{id_animal}/diagnosticos",
    response_model=DiagnosticoResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_diagnostico(
    id_animal: int,
    diagnostico_in: DiagnosticoCreate,
    db: Session = Depends(get_db),
    usuario: dict = Depends(verificar_acceso_modulo),
):
    # Quien registra el diagnóstico es el usuario del token, no un dato que envíe el cliente
    return DiagnosticoService.crear_diagnostico(db, id_animal, usuario["id_usuario"], diagnostico_in)


@router.put("/diagnosticos/{id_diagnostico}", response_model=DiagnosticoResponse)
def actualizar_diagnostico(
    id_diagnostico: int,
    diagnostico_in: DiagnosticoUpdate,
    db: Session = Depends(get_db),
):
    return DiagnosticoService.actualizar_diagnostico(db, id_diagnostico, diagnostico_in)
