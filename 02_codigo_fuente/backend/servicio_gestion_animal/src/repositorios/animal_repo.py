from sqlalchemy.orm import Session
from src.modelos.animal_model import AnimalModel

class AnimalRepository:
    @staticmethod
    def obtener_todos(db: Session):
        return db.query(AnimalModel).order_by(AnimalModel.codigo_animal).all()

    @staticmethod
    def obtener_por_id(db: Session, id_animal: int):
        return db.query(AnimalModel).filter(AnimalModel.id_animal == id_animal).first()

    @staticmethod
    def obtener_por_codigo(db: Session, codigo_animal: str):
        return db.query(AnimalModel).filter(AnimalModel.codigo_animal == codigo_animal).first()

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
