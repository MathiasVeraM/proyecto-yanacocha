from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from src.database import get_db
from src.esquemas.taxonomia_schema import (
    SugerenciaTaxonomia, TaxonomiaCreate, TaxonomiaImportar, TaxonomiaResponse, TaxonomiaUpdate
)
from src.logica_negocio.auth import verificar_acceso_modulo
from src.logica_negocio.taxonomia_service import TaxonomiaService

router = APIRouter(
    prefix="/api/animales/taxonomia",
    tags=["Gestión Animal - Taxonomía"],
    dependencies=[Depends(verificar_acceso_modulo)],
)

@router.get("", response_model=List[TaxonomiaResponse])
def listar_taxonomia(buscar: Optional[str] = None, db: Session = Depends(get_db)):
    return TaxonomiaService.buscar(db, buscar)

@router.get("/sugerencias", response_model=List[SugerenciaTaxonomia])
def sugerir_especies(buscar: str = Query(min_length=2), db: Session = Depends(get_db)):
    # Autocompletado al escribir el nombre común: catálogo propio + iNaturalist
    return TaxonomiaService.sugerencias(db, buscar.strip())

@router.post("/importar", response_model=TaxonomiaResponse)
def importar_especie(datos: TaxonomiaImportar, db: Session = Depends(get_db)):
    # Si ya se había importado devuelve la existente, por eso no es 201
    return TaxonomiaService.importar_de_inaturalist(db, datos.id_inaturalist)

@router.post("", response_model=TaxonomiaResponse, status_code=status.HTTP_201_CREATED)
def crear_taxonomia(taxonomia_in: TaxonomiaCreate, db: Session = Depends(get_db)):
    return TaxonomiaService.crear_taxonomia(db, taxonomia_in)

@router.put("/{id_taxonomia}", response_model=TaxonomiaResponse)
def actualizar_taxonomia(id_taxonomia: int, taxonomia_in: TaxonomiaUpdate, db: Session = Depends(get_db)):
    return TaxonomiaService.actualizar_taxonomia(db, id_taxonomia, taxonomia_in)
