from typing import List, Optional
from fastapi import APIRouter, Depends, File, Query, Response, UploadFile, status
from sqlalchemy.orm import Session
from src.database import get_db
from src.esquemas.animal_schema import AnimalCreate, AnimalResponse, AnimalUpdate, EstadoAnimal
from src.esquemas.diagnostico_schema import DiagnosticoCreate, DiagnosticoResponse, DiagnosticoUpdate
from src.esquemas.tratamiento_schema import TratamientoCreate, TratamientoResponse, TratamientoUpdate
from src.logica_negocio.auth import verificar_acceso_modulo
from src.logica_negocio.animal_service import AnimalService
from src.logica_negocio.diagnostico_service import DiagnosticoService
from src.logica_negocio.imagen_service import ImagenService
from src.logica_negocio.tratamiento_service import TratamientoService

# Todas las rutas exigen token válido y permiso sobre el módulo de gestión animal
router = APIRouter(
    prefix="/api/animales",
    tags=["Gestión Animal"],
    dependencies=[Depends(verificar_acceso_modulo)],
)

# --- ANIMALES ---

@router.get("", response_model=List[AnimalResponse])
def listar_animales(
    buscar: Optional[str] = Query(None, description="Código o nombre común"),
    id_taxonomia: Optional[int] = Query(None, description="Filtra por especie"),
    estado: Optional[EstadoAnimal] = None,
    id_recinto: Optional[int] = None,
    db: Session = Depends(get_db),
):
    return AnimalService.listar_animales(db, buscar, id_taxonomia, estado, id_recinto)

@router.post("", response_model=AnimalResponse, status_code=status.HTTP_201_CREATED)
def crear_animal(animal_in: AnimalCreate, db: Session = Depends(get_db)):
    return AnimalService.crear_animal(db, animal_in)

@router.get("/{id_animal}", response_model=AnimalResponse)
def obtener_animal(id_animal: int, db: Session = Depends(get_db)):
    return AnimalService.animal_o_404(db, id_animal)

@router.put("/{id_animal}", response_model=AnimalResponse)
def actualizar_animal(id_animal: int, animal_in: AnimalUpdate, db: Session = Depends(get_db)):
    return AnimalService.actualizar_animal(db, id_animal, animal_in)

# --- FOTOGRAFÍA ---

@router.put("/{id_animal}/imagen", response_model=AnimalResponse)
def subir_imagen(id_animal: int, archivo: UploadFile = File(...), db: Session = Depends(get_db)):
    # Sube o reemplaza la foto (JPG, PNG o WEBP, máx. 5 MB) y actualiza url_imagen
    return ImagenService.guardar_imagen(db, id_animal, archivo.file)

@router.get("/{id_animal}/imagen", response_class=Response)
def obtener_imagen(id_animal: int, db: Session = Depends(get_db)):
    imagen = ImagenService.obtener_imagen(db, id_animal)
    # La URL cambia en cada subida (?v=...), así que el navegador puede guardarla en caché
    return Response(
        content=imagen.contenido,
        media_type=imagen.tipo_mime,
        headers={"Cache-Control": "private, max-age=86400"},
    )

# No hay DELETE: ningún animal se elimina físicamente (trazabilidad, HU-02); se cambia su estado_actual

# --- DIAGNÓSTICOS ---

@router.get("/{id_animal}/diagnosticos", response_model=List[DiagnosticoResponse])
def listar_diagnosticos(id_animal: int, db: Session = Depends(get_db)):
    return DiagnosticoService.listar_por_animal(db, id_animal)

@router.post(
    "/{id_animal}/diagnosticos", response_model=DiagnosticoResponse, status_code=status.HTTP_201_CREATED
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
def actualizar_diagnostico(id_diagnostico: int, diagnostico_in: DiagnosticoUpdate, db: Session = Depends(get_db)):
    return DiagnosticoService.actualizar_diagnostico(db, id_diagnostico, diagnostico_in)

# --- TRATAMIENTOS ---

@router.get("/diagnosticos/{id_diagnostico}/tratamientos", response_model=List[TratamientoResponse])
def listar_tratamientos(id_diagnostico: int, db: Session = Depends(get_db)):
    return TratamientoService.listar_por_diagnostico(db, id_diagnostico)

@router.post(
    "/diagnosticos/{id_diagnostico}/tratamientos",
    response_model=TratamientoResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_tratamiento(id_diagnostico: int, tratamiento_in: TratamientoCreate, db: Session = Depends(get_db)):
    return TratamientoService.crear_tratamiento(db, id_diagnostico, tratamiento_in)

@router.put("/tratamientos/{id_tratamiento}", response_model=TratamientoResponse)
def actualizar_tratamiento(id_tratamiento: int, tratamiento_in: TratamientoUpdate, db: Session = Depends(get_db)):
    return TratamientoService.actualizar_tratamiento(db, id_tratamiento, tratamiento_in)
