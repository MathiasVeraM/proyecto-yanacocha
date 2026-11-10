from datetime import date

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.modelos.actividad_model import ActividadModel
from src.modelos.actividad_alimentacion_model import ActividadAlimentacionModel
from src.modelos.dieta_model import DietaModel
from src.modelos.dieta_alimento_model import DietaAlimentoModel


class DietaRepository:
    @staticmethod
    def obtener_por_id(db: Session, id_dieta: int) -> DietaModel | None:
        return db.query(DietaModel).filter(DietaModel.id_dieta == id_dieta).first()

    @staticmethod
    def obtener_por_animal(db: Session, id_animal: int) -> list[DietaModel]:
        return (
            db.query(DietaModel)
            .filter(DietaModel.id_animal == id_animal)
            .order_by(DietaModel.fecha_inicio.desc(), DietaModel.id_dieta.desc())
            .all()
        )

    @staticmethod
    def obtener_vigente(db: Session, id_animal: int) -> DietaModel | None:
        return (
            db.query(DietaModel)
            .filter(DietaModel.id_animal == id_animal, DietaModel.vigente.is_(True))
            .first()
        )

    @staticmethod
    def listar_vigentes(db: Session) -> list[DietaModel]:
        return db.query(DietaModel).filter(DietaModel.vigente.is_(True)).all()

    @staticmethod
    def crear_dieta(db: Session, datos: dict, alimentos: list[dict]) -> DietaModel:
        try:
            anterior = DietaRepository.obtener_vigente(db, datos["id_animal"])
            if anterior is not None:
                anterior.vigente = False
                anterior.fecha_fin = max(
                    anterior.fecha_inicio,
                    datos["fecha_inicio"] - date.resolution,
                )
                db.flush()
                DietaRepository.cancelar_tomas_pendientes(
                    db,
                    anterior.id_dieta,
                    datos["fecha_inicio"],
                )

            dieta = DietaModel(**datos)
            dieta.alimentos = [DietaAlimentoModel(**alimento) for alimento in alimentos]
            db.add(dieta)
            db.commit()
            db.refresh(dieta)
        except SQLAlchemyError:
            db.rollback()
            raise
        return dieta

    @staticmethod
    def cancelar_tomas_pendientes(db: Session, id_dieta: int, desde: date) -> None:
        actividades = (
            db.query(ActividadModel)
            .join(
                ActividadAlimentacionModel,
                ActividadAlimentacionModel.id_actividad == ActividadModel.id_actividad,
            )
            .filter(
                ActividadAlimentacionModel.id_dieta == id_dieta,
                ActividadModel.fecha_programada >= desde,
                ActividadModel.completada.is_(False),
            )
            .all()
        )
        for actividad in actividades:
            db.delete(actividad.alimentacion)
            db.delete(actividad)
