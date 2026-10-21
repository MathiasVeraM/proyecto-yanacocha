from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.logica_negocio.codigo_animal import iniciales, siguiente_codigo
from src.logica_negocio.utilidades import datos_a_actualizar
from src.repositorios.animal_repo import AnimalRepository
from src.repositorios.recinto_repo import RecintoRepository
from src.repositorios.taxonomia_repo import TaxonomiaRepository

CAMPOS_OBLIGATORIOS = {"id_recinto", "estado_actual", "fecha_ingreso"}
# Si dos personas registran a la vez un animal de la misma especie, el segundo reintenta con el siguiente número
INTENTOS_CODIGO = 3

def _validar_recinto(db: Session, id_recinto: int):
    if not RecintoRepository.obtener_por_id(db, id_recinto):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El recinto indicado no existe"
        )

class AnimalService:
    @staticmethod
    def animal_o_404(db: Session, id_animal: int):
        animal = AnimalRepository.obtener_por_id(db, id_animal)
        if not animal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Animal no encontrado")
        return animal

    @staticmethod
    def listar_animales(db: Session, buscar=None, id_taxonomia=None, estado=None, id_recinto=None):
        return AnimalRepository.obtener_todos(db, buscar, id_taxonomia, estado, id_recinto)

    @staticmethod
    def crear_animal(db: Session, animal_in):
        taxonomia = TaxonomiaRepository.obtener_por_id(db, animal_in.id_taxonomia)
        if not taxonomia:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La especie indicada no existe en el catálogo"
            )
        _validar_recinto(db, animal_in.id_recinto)

        prefijo = iniciales(taxonomia.especie)
        # exclude_none: los campos no enviados toman su valor por defecto (ej. fecha de hoy)
        datos = animal_in.model_dump(exclude_none=True)
        for _ in range(INTENTOS_CODIGO):
            codigos = AnimalRepository.obtener_codigos_con_prefijo(db, prefijo)
            datos["codigo_animal"] = siguiente_codigo(prefijo, codigos)
            try:
                return AnimalRepository.crear_animal(db, datos)
            except IntegrityError:
                # Otro registro tomó ese código justo antes: se recalcula
                db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se pudo generar un código único para el animal; intenta de nuevo"
        )

    @staticmethod
    def actualizar_animal(db: Session, id_animal: int, animal_in):
        animal = AnimalService.animal_o_404(db, id_animal)
        datos = datos_a_actualizar(animal_in, CAMPOS_OBLIGATORIOS)
        if "id_recinto" in datos:
            _validar_recinto(db, datos["id_recinto"])
        return AnimalRepository.actualizar_animal(db, animal, datos)
