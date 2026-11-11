from datetime import date, datetime, time

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.modelos.actividad_model import ActividadModel
from src.modelos.actividad_alimentacion_model import ActividadAlimentacionModel


class ActividadRepository:
    @staticmethod
    def obtener_por_id(db: Session, id_actividad: int) -> ActividadModel | None:
        return (
            db.query(ActividadModel)
            .filter(ActividadModel.id_actividad == id_actividad)
            .first()
        )

    @staticmethod
    def listar(
        db: Session,
        id_animal: int | None = None,
        id_recinto: int | None = None,
        tipo_actividad: str | None = None,
        completada: bool | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
    ) -> list[ActividadModel]:
        consulta = db.query(ActividadModel)
        if id_animal is not None:
            consulta = consulta.filter(ActividadModel.id_animal == id_animal)
        if id_recinto is not None:
            consulta = consulta.filter(ActividadModel.id_recinto == id_recinto)
        if tipo_actividad is not None:
            consulta = consulta.filter(ActividadModel.tipo_actividad == tipo_actividad)
        if completada is not None:
            consulta = consulta.filter(ActividadModel.completada.is_(completada))
        if fecha_desde is not None:
            consulta = consulta.filter(ActividadModel.fecha_programada >= fecha_desde)
        if fecha_hasta is not None:
            consulta = consulta.filter(ActividadModel.fecha_programada <= fecha_hasta)
        return consulta.order_by(
            ActividadModel.fecha_programada,
            ActividadModel.hora_programada,
            ActividadModel.id_actividad,
        ).all()

    @staticmethod
    def crear(
        db: Session,
        datos: dict,
        detalle: dict | None = None,
    ) -> ActividadModel:
        try:
            actividad = ActividadModel(**datos)
            db.add(actividad)
            db.flush()
            if detalle is not None:
                detalle_modelo = detalle.pop("_modelo")
                db.add(detalle_modelo(id_actividad=actividad.id_actividad, **detalle))
            db.commit()
            db.refresh(actividad)
        except SQLAlchemyError:
            db.rollback()
            raise
        return actividad

    @staticmethod
    def obtener_toma(
        db: Session,
        id_dieta: int,
        fecha: date,
        hora: time,
    ) -> ActividadModel | None:
        return (
            db.query(ActividadModel)
            .join(
                ActividadAlimentacionModel,
                ActividadAlimentacionModel.id_actividad == ActividadModel.id_actividad,
            )
            .filter(
                ActividadAlimentacionModel.id_dieta == id_dieta,
                ActividadModel.fecha_programada == fecha,
                ActividadModel.hora_programada == hora,
            )
            .first()
        )

    @staticmethod
    def completar(
        db: Session,
        actividad: ActividadModel,
        id_usuario: int,
        observaciones: str | None,
        actualizar_observaciones: bool,
        fecha_completada: datetime,
    ) -> ActividadModel:
        try:
            actividad.completada = True
            actividad.id_usuario_completo = id_usuario
            actividad.fecha_completada = fecha_completada
            if actualizar_observaciones:
                actividad.observaciones = observaciones
            db.commit()
            db.refresh(actividad)
        except SQLAlchemyError:
            db.rollback()
            raise
        return actividad

    @staticmethod
    def reabrir(db: Session, actividad: ActividadModel) -> ActividadModel:
        # Conserva las observaciones registradas al completar.
        try:
            actividad.completada = False
            actividad.id_usuario_completo = None
            actividad.fecha_completada = None
            db.commit()
            db.refresh(actividad)
        except SQLAlchemyError:
            db.rollback()
            raise
        return actividad


def actividad_a_dict(actividad: ActividadModel) -> dict:
    resultado = {
        "id_actividad": actividad.id_actividad,
        "tipo_actividad": actividad.tipo_actividad,
        "id_animal": actividad.id_animal,
        "id_recinto": actividad.id_recinto,
        "fecha_programada": actividad.fecha_programada,
        "hora_programada": actividad.hora_programada,
        "duracion_horas": actividad.duracion_horas,
        "duracion_minutos": actividad.duracion_minutos,
        "id_usuario_programo": actividad.id_usuario_programo,
        "fecha_registro": actividad.fecha_registro,
        "completada": actividad.completada,
        "observaciones": actividad.observaciones,
        "id_usuario_completo": actividad.id_usuario_completo,
        "fecha_completada": actividad.fecha_completada,
        "id_dieta": None,
        "tipo_enriquecimiento": None,
        "descripcion_estimulo": None,
        "objetivo_entrenamiento": None,
        "tipo_refuerzo": None,
        "cancelada": False,
    }
    if actividad.alimentacion is not None:
        resultado["id_dieta"] = actividad.alimentacion.id_dieta
    if actividad.enriquecimiento is not None:
        resultado["tipo_enriquecimiento"] = actividad.enriquecimiento.tipo_enriquecimiento
        resultado["descripcion_estimulo"] = actividad.enriquecimiento.descripcion_estimulo
    if actividad.entrenamiento is not None:
        resultado["objetivo_entrenamiento"] = actividad.entrenamiento.objetivo_entrenamiento
        resultado["tipo_refuerzo"] = actividad.entrenamiento.tipo_refuerzo
    return resultado
