from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from src.modelos.animal_model import AnimalModel
from src.modelos.diagnostico_model import DiagnosticoModel
from src.modelos.fechas import hoy_local
from src.modelos.tratamiento_model import (
    ESTADOS_EN_CENTRO,
    TratamientoMedicamentoModel,
    TratamientoModel,
    condiciones_tratamiento_vigente,
)


class TratamientoRepository:
    @staticmethod
    def contar_animales_con_tratamiento_en_curso(db: Session) -> int:
        # Mismo criterio que la alerta de cada animal (AnimalModel.tiene_tratamiento_en_curso):
        # no cuentan los vencidos ni los de animales que ya salieron del centro
        return (
            db.query(func.count(func.distinct(DiagnosticoModel.id_animal)))
            .join(
                TratamientoModel,
                TratamientoModel.id_diagnostico == DiagnosticoModel.id_diagnostico,
            )
            .join(AnimalModel, AnimalModel.id_animal == DiagnosticoModel.id_animal)
            .filter(
                *condiciones_tratamiento_vigente(hoy_local()),
                AnimalModel.estado_actual.in_(ESTADOS_EN_CENTRO),
            )
            .scalar()
            or 0
        )

    @staticmethod
    def obtener_por_diagnostico(db: Session, id_diagnostico: int):
        return (
            db.query(TratamientoModel)
            .filter(TratamientoModel.id_diagnostico == id_diagnostico)
            .order_by(TratamientoModel.fecha_inicio.desc(), TratamientoModel.id_tratamiento.desc())
            .all()
        )

    @staticmethod
    def obtener_por_animal(db: Session, id_animal: int):
        # Una consulta con JOIN (más una para los medicamentos), sin importar cuántos diagnósticos tenga
        return (
            db.query(TratamientoModel)
            .join(DiagnosticoModel, DiagnosticoModel.id_diagnostico == TratamientoModel.id_diagnostico)
            .filter(DiagnosticoModel.id_animal == id_animal)
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
