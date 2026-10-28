from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, contains_eager

from src.modelos.diagnostico_model import DiagnosticoModel
from src.modelos.signos_vitales_model import SignosVitalesModel


class DiagnosticoRepository:
    @staticmethod
    def obtener_por_animal(db: Session, id_animal: int):
        # Los más recientes primero, como un historial clínico
        return (
            db.query(DiagnosticoModel)
            .filter(DiagnosticoModel.id_animal == id_animal)
            .order_by(DiagnosticoModel.fecha_registro.desc(), DiagnosticoModel.id_diagnostico.desc())
            .all()
        )

    @staticmethod
    def obtener_por_id(db: Session, id_diagnostico: int):
        return (
            db.query(DiagnosticoModel)
            .filter(DiagnosticoModel.id_diagnostico == id_diagnostico)
            .first()
        )

    @staticmethod
    def crear_diagnostico(db: Session, diagnostico_data: dict, signos_vitales_data: dict | None = None):
        diagnostico = DiagnosticoModel(**diagnostico_data)
        if signos_vitales_data is not None:
            diagnostico.signos_vitales = SignosVitalesModel(**signos_vitales_data)
        db.add(diagnostico)
        try:
            db.commit()
            db.refresh(diagnostico)
        except SQLAlchemyError:
            db.rollback()
            raise
        return diagnostico

    @staticmethod
    def actualizar_diagnostico(db: Session, diagnostico: DiagnosticoModel, datos: dict):
        for campo, valor in datos.items():
            setattr(diagnostico, campo, valor)
        db.commit()
        db.refresh(diagnostico)
        return diagnostico

    @staticmethod
    def obtener_signos_vitales_por_animal(db: Session, id_animal: int):
        return (
            db.query(SignosVitalesModel)
            .join(SignosVitalesModel.diagnostico)
            .options(contains_eager(SignosVitalesModel.diagnostico))
            .filter(DiagnosticoModel.id_animal == id_animal)
            .order_by(DiagnosticoModel.fecha_registro.desc(), DiagnosticoModel.id_diagnostico.desc())
            .all()
        )
