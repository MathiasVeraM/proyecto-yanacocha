from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.esquemas.tratamiento_schema import TratamientoCreate, TratamientoResponse, TratamientoUpdate
from src.logica_negocio.auth import verificar_acceso_modulo
from src.logica_negocio import actividades_client
from src.logica_negocio.tratamiento_service import TratamientoService

router = APIRouter(
    prefix="/api/animales",
    tags=["Tratamientos Veterinarios"],
    dependencies=[Depends(verificar_acceso_modulo)],
)


@router.get("/metricas/animales-con-tratamiento-en-curso", response_model=int)
def contar_animales_con_tratamiento_en_curso(db: Session = Depends(get_db)):
    return TratamientoService.contar_animales_con_tratamiento_en_curso(db)


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


@router.post("/tratamientos/{id_tratamiento}/generar-actividades")
def generar_actividades_tratamiento(
    id_tratamiento: int,
    request: Request,
    db: Session = Depends(get_db),
):
    TratamientoService._tratamiento_o_404(db, id_tratamiento)
    autorizacion = request.headers.get("authorization")
    if autorizacion is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere un token de acceso",
        )
    return actividades_client.generar_actividades_tratamiento(
        id_tratamiento,
        autorizacion,
    )
