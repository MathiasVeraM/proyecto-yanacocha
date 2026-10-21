from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.logica_negocio.utilidades import datos_a_actualizar
from src.repositorios.animal_repo import AnimalRepository
from src.repositorios.diagnostico_repo import DiagnosticoRepository

CAMPOS_OBLIGATORIOS = {"codigo_animal", "nombre_comun", "estado_actual", "fecha_ingreso"}

class AnimalService:
    @staticmethod
    def animal_o_404(db: Session, id_animal: int):
        animal = AnimalRepository.obtener_por_id(db, id_animal)
        if not animal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Animal no encontrado")
        return animal

    @staticmethod
    def _validar_codigo_libre(db: Session, codigo_animal: str):
        if AnimalRepository.obtener_por_codigo(db, codigo_animal):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un animal con ese código"
            )

    @staticmethod
    def listar_animales(db: Session):
        return AnimalRepository.obtener_todos(db)

    @staticmethod
    def crear_animal(db: Session, animal_in):
        AnimalService._validar_codigo_libre(db, animal_in.codigo_animal)
        # exclude_none: los campos no enviados toman su valor por defecto (ej. fecha de hoy)
        return AnimalRepository.crear_animal(db, animal_in.model_dump(exclude_none=True))

    @staticmethod
    def actualizar_animal(db: Session, id_animal: int, animal_in):
        animal = AnimalService.animal_o_404(db, id_animal)
        datos = datos_a_actualizar(animal_in, CAMPOS_OBLIGATORIOS)
        codigo = datos.get("codigo_animal")
        if codigo and codigo != animal.codigo_animal:
            AnimalService._validar_codigo_libre(db, codigo)
        return AnimalRepository.actualizar_animal(db, animal, datos)

    @staticmethod
    def eliminar_animal(db: Session, id_animal: int):
        animal = AnimalService.animal_o_404(db, id_animal)
        # Solo se borran registros hechos por error; el historial clínico nunca se pierde
        if DiagnosticoRepository.contar_por_animal(db, id_animal) > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El animal tiene diagnósticos registrados; cambia su estado en lugar de eliminarlo"
            )
        AnimalRepository.eliminar_animal(db, animal)
