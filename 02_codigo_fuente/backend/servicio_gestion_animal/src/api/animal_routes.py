from typing import List, Optional
from fastapi import APIRouter, Depends, File, Query, Response, UploadFile, status
from sqlalchemy.orm import Session
from src.database import get_db
from src.esquemas.animal_schema import AnimalCreate, AnimalResponse, AnimalUpdate, EstadoAnimal
from src.logica_negocio.auth import verificar_acceso_modulo
from src.logica_negocio.animal_service import AnimalService
from src.logica_negocio.imagen_service import ImagenService

# Todas las rutas de animales exigen token válido y permiso sobre el módulo de gestión animal
router = APIRouter(
    prefix="/api/animales",
    tags=["Gestión Animal"],
    dependencies=[Depends(verificar_acceso_modulo)],
)

@router.get("", response_model=List[AnimalResponse])
def listar_animales(
    buscar: Optional[str] = Query(None, description="Código, nombre del ejemplar o nombre común"),
    id_taxonomia: Optional[int] = Query(None, description="Filtra por especie"),
    estado: Optional[EstadoAnimal] = None,
    id_recinto: Optional[int] = None,
    clase: Optional[str] = Query(None, description="Clase taxonómica, ej. Mammalia, Aves, Reptilia"),
    db: Session = Depends(get_db),
):
    return AnimalService.listar_animales(db, buscar, id_taxonomia, estado, id_recinto, clase)

@router.post("", response_model=AnimalResponse, status_code=status.HTTP_201_CREATED)
def crear_animal(animal_in: AnimalCreate, db: Session = Depends(get_db)):
    return AnimalService.crear_animal(db, animal_in)

@router.get("/{id_animal}", response_model=AnimalResponse)
def obtener_animal(id_animal: int, db: Session = Depends(get_db)):
    return AnimalService.animal_o_404(db, id_animal)

@router.put("/{id_animal}", response_model=AnimalResponse)
def actualizar_animal(id_animal: int, animal_in: AnimalUpdate, db: Session = Depends(get_db)):
    return AnimalService.actualizar_animal(db, id_animal, animal_in)

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
