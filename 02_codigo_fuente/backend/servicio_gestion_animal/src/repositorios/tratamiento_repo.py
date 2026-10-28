from sqlalchemy.orm import Session
from src.modelos.tratamiento_model import TratamientoModel

class TratamientoRepository:
    @staticmethod
    def obtener_por_diagnostico(db: Session, id_diagnostico: int):
        return (
            db.query(TratamientoModel)
            .filter(TratamientoModel.id_diagnostico == id_diagnostico)
            .order_by(TratamientoModel.fecha_inicio.desc(), TratamientoModel.id_tratamiento.desc())
            .all()
        )

    @staticmethod
    def obtener_por_id(db: Session, id_tratamiento: int):
        return (
            db.query(TratamientoModel)
            .filter(TratamientoModel.id_tratamiento == id_tratamiento)
            .first()
        )

    @staticmethod
    def crear_tratamiento(db: Session, tratamiento_data: dict):
        tratamiento = TratamientoModel(**tratamiento_data)
        db.add(tratamiento)
        db.commit()
        db.refresh(tratamiento)
        return tratamiento

    @staticmethod
    def actualizar_tratamiento(db: Session, tratamiento: TratamientoModel, datos: dict):
        for campo, valor in datos.items():
            setattr(tratamiento, campo, valor)
        db.commit()
        db.refresh(tratamiento)
        return tratamiento
