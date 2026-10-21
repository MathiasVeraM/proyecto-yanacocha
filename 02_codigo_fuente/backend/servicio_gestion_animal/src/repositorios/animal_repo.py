from sqlalchemy.orm import Session
from src.modelos.animal_model import AnimalModel, TaxonomiaModel

class AnimalRepository:
    @staticmethod
    def obtener_todos(
        db: Session,
        buscar: str | None = None,
        id_taxonomia: int | None = None,
        estado: str | None = None,
        id_recinto: int | None = None,
    ):
        # Todos los filtros son opcionales y se combinan entre sí
        consulta = db.query(AnimalModel)
        if buscar:
            patron = f"%{buscar}%"
            consulta = consulta.join(AnimalModel.taxonomia).filter(
                AnimalModel.codigo_animal.ilike(patron) | TaxonomiaModel.nombre_comun.ilike(patron)
            )
        if id_taxonomia is not None:
            consulta = consulta.filter(AnimalModel.id_taxonomia == id_taxonomia)
        if estado:
            consulta = consulta.filter(AnimalModel.estado_actual == estado)
        if id_recinto is not None:
            consulta = consulta.filter(AnimalModel.id_recinto == id_recinto)
        return consulta.order_by(AnimalModel.codigo_animal).all()

    @staticmethod
    def obtener_por_id(db: Session, id_animal: int):
        return db.query(AnimalModel).filter(AnimalModel.id_animal == id_animal).first()

    @staticmethod
    def obtener_por_codigo(db: Session, codigo_animal: str):
        return db.query(AnimalModel).filter(AnimalModel.codigo_animal == codigo_animal).first()

    @staticmethod
    def obtener_codigos_con_prefijo(db: Session, prefijo: str) -> list[str]:
        filas = (
            db.query(AnimalModel.codigo_animal)
            .filter(AnimalModel.codigo_animal.like(f"{prefijo}-%"))
            .all()
        )
        return [fila.codigo_animal for fila in filas]

    @staticmethod
    def crear_animal(db: Session, animal_data: dict):
        animal = AnimalModel(**animal_data)
        db.add(animal)
        db.commit()
        db.refresh(animal)
        return animal

    @staticmethod
    def actualizar_animal(db: Session, animal: AnimalModel, datos: dict):
        for campo, valor in datos.items():
            setattr(animal, campo, valor)
        db.commit()
        db.refresh(animal)
        return animal
