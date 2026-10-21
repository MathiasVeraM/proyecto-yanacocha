from sqlalchemy.orm import Session
from src.modelos.animal_model import DiagnosticoModel

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
    def crear_diagnostico(db: Session, diagnostico_data: dict):
        diagnostico = DiagnosticoModel(**diagnostico_data)
        db.add(diagnostico)
        db.commit()
        db.refresh(diagnostico)
        return diagnostico

    @staticmethod
    def actualizar_diagnostico(db: Session, diagnostico: DiagnosticoModel, datos: dict):
        for campo, valor in datos.items():
            setattr(diagnostico, campo, valor)
        db.commit()
        db.refresh(diagnostico)
        return diagnostico
