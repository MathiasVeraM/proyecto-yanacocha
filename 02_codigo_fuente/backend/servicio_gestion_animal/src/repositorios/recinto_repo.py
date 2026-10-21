from sqlalchemy.orm import Session
from src.modelos.animal_model import RecintoModel

class RecintoRepository:
    @staticmethod
    def obtener_todos(db: Session):
        return db.query(RecintoModel).order_by(RecintoModel.nombre_recinto).all()

    @staticmethod
    def obtener_por_id(db: Session, id_recinto: int):
        return db.query(RecintoModel).filter(RecintoModel.id_recinto == id_recinto).first()

    @staticmethod
    def obtener_por_nombre(db: Session, nombre_recinto: str):
        return db.query(RecintoModel).filter(RecintoModel.nombre_recinto == nombre_recinto).first()

    @staticmethod
    def crear_recinto(db: Session, recinto_data: dict):
        recinto = RecintoModel(**recinto_data)
        db.add(recinto)
        db.commit()
        db.refresh(recinto)
        return recinto

    @staticmethod
    def actualizar_recinto(db: Session, recinto: RecintoModel, datos: dict):
        for campo, valor in datos.items():
            setattr(recinto, campo, valor)
        db.commit()
        db.refresh(recinto)
        return recinto
