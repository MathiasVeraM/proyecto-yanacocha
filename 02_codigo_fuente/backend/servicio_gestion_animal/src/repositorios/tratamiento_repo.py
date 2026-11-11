from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from src.modelos.tratamiento_model import TratamientoMedicamentoModel, TratamientoModel


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
    def crear_tratamiento(db: Session, tratamiento_data: dict, medicamentos: list[dict] | None = None):
        tratamiento = TratamientoModel(
            **tratamiento_data,
            medicamentos=[
                TratamientoMedicamentoModel(**medicamento)
                for medicamento in (medicamentos or [])
            ],
        )
        try:
            db.add(tratamiento)
            db.commit()
            db.refresh(tratamiento)
        except SQLAlchemyError:
            db.rollback()
            raise
        return tratamiento

    @staticmethod
    def actualizar_tratamiento(db: Session, tratamiento: TratamientoModel, datos: dict):
        medicamentos = datos.pop("medicamentos", None)
        try:
            for campo, valor in datos.items():
                setattr(tratamiento, campo, valor)
            if medicamentos is not None:
                tratamiento.medicamentos = [
                    TratamientoMedicamentoModel(**medicamento)
                    for medicamento in medicamentos
                ]
            db.commit()
            db.refresh(tratamiento)
        except SQLAlchemyError:
            db.rollback()
            raise
        return tratamiento
