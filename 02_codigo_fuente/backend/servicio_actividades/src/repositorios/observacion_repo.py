from datetime import date

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.modelos.actividad_model import ActividadModel
from src.modelos.observacion_actividad_model import ObservacionActividadModel


class ObservacionRepository:
    @staticmethod
    def crear(db: Session, datos: dict) -> ObservacionActividadModel:
        try:
            observacion = ObservacionActividadModel(**datos)
            db.add(observacion)
            db.commit()
            db.refresh(observacion)
        except SQLAlchemyError:
            db.rollback()
            raise
        return observacion

    @staticmethod
    def listar_por_actividad(
        db: Session,
        id_actividad: int,
    ) -> list[ObservacionActividadModel]:
        return (
            db.query(ObservacionActividadModel)
            .filter(ObservacionActividadModel.id_actividad == id_actividad)
            .order_by(
                ObservacionActividadModel.fecha_registro,
                ObservacionActividadModel.id_observacion,
            )
            .all()
        )

    @staticmethod
    def listar_por_fechas(
        db: Session,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
    ) -> list[ObservacionActividadModel]:
        consulta = db.query(ObservacionActividadModel).join(
            ActividadModel,
            ActividadModel.id_actividad == ObservacionActividadModel.id_actividad,
        )
        if fecha_desde is not None:
            consulta = consulta.filter(ActividadModel.fecha_programada >= fecha_desde)
        if fecha_hasta is not None:
            consulta = consulta.filter(ActividadModel.fecha_programada <= fecha_hasta)
        return consulta.order_by(
            ObservacionActividadModel.fecha_registro,
            ObservacionActividadModel.id_observacion,
        ).all()
