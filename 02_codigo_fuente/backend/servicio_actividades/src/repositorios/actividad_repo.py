from datetime import date, datetime, time

from sqlalchemy import exists, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.database import Base
from src.modelos.actividad_model import ActividadModel
from src.modelos.actividad_alimentacion_model import ActividadAlimentacionModel
from src.modelos.actividad_tratamiento_model import (
    SEPARADOR_DOSIS,
    SEPARADOR_MEDICAMENTOS,
    ActividadTratamientoModel,
)
from src.modelos.observacion_actividad_model import ObservacionActividadModel
from src.modelos.referencias_model import ESTADOS_EN_CENTRO


def _dosis_visible():
    """Condición para mostrar una dosis de tratamiento en el listado y el calendario.

    Las pendientes solo se muestran si su tratamiento sigue en curso y el animal sigue en el
    centro; las completadas se conservan como historial. Va dentro de la misma consulta del
    listado (EXISTS por clave primaria), sin consultas aparte.
    """
    tratamiento = Base.metadata.tables["gestion_animal.tratamiento"]
    animal = Base.metadata.tables["gestion_animal.animal"]
    dosis_vigente = exists().where(
        ActividadTratamientoModel.id_actividad == ActividadModel.id_actividad,
        tratamiento.c.id_tratamiento == ActividadTratamientoModel.id_tratamiento,
        tratamiento.c.estado == "en_curso",
        animal.c.id_animal == ActividadModel.id_animal,
        animal.c.estado_actual.in_(ESTADOS_EN_CENTRO),
    )
    return or_(
        ActividadModel.tipo_actividad != "tratamiento",
        ActividadModel.completada.is_(True),
        dosis_vigente,
    )


def medicamentos_de_texto(texto: str | None) -> list[dict]:
    """Convierte los medicamentos agregados por la base en una lista ordenada por nombre."""
    if not texto:
        return []
    medicamentos = []
    for item in texto.split(SEPARADOR_MEDICAMENTOS):
        nombre, _, dosis = item.partition(SEPARADOR_DOSIS)
        medicamentos.append({"nombre_medicamento": nombre, "dosis_ml": float(dosis)})
    return sorted(medicamentos, key=lambda medicamento: medicamento["nombre_medicamento"].lower())


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
        consulta = db.query(ActividadModel).filter(_dosis_visible())
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
    def crear_varias(db: Session, filas: list[tuple[dict, dict | None]]) -> list[ActividadModel]:
        """Crea varias actividades (con su detalle) con un solo guardado. filas: (datos, detalle)."""
        actividades = []
        try:
            for datos, detalle in filas:
                actividad = ActividadModel(**datos)
                if detalle is not None:
                    modelo = detalle.pop("_modelo")
                    relacion = {
                        "ActividadAlimentacionModel": "alimentacion",
                        "ActividadEnriquecimientoModel": "enriquecimiento",
                        "ActividadEntrenamientoModel": "entrenamiento",
                    }[modelo.__name__]
                    setattr(actividad, relacion, modelo(**detalle))
                actividades.append(actividad)
            db.add_all(actividades)
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            raise
        # Se vuelven a leer en una sola consulta (con su id y su detalle)
        ids = [actividad.id_actividad for actividad in actividades]
        return (
            db.query(ActividadModel)
            .filter(ActividadModel.id_actividad.in_(ids))
            .order_by(ActividadModel.fecha_programada, ActividadModel.hora_programada)
            .all()
        )

    @staticmethod
    def actualizar(
        db: Session,
        actividad: ActividadModel,
        campos: dict,
        campos_detalle: dict,
    ) -> ActividadModel:
        try:
            for campo, valor in campos.items():
                setattr(actividad, campo, valor)
            detalle = actividad.alimentacion or actividad.enriquecimiento or actividad.entrenamiento
            if detalle is not None:
                for campo, valor in campos_detalle.items():
                    setattr(detalle, campo, valor)
            db.commit()
            db.refresh(actividad)
        except SQLAlchemyError:
            db.rollback()
            raise
        return actividad

    @staticmethod
    def eliminar(db: Session, actividad: ActividadModel) -> None:
        """Borra la actividad, su detalle y sus observaciones."""
        try:
            db.query(ObservacionActividadModel).filter(
                ObservacionActividadModel.id_actividad == actividad.id_actividad
            ).delete(synchronize_session=False)
            for detalle in (actividad.alimentacion, actividad.enriquecimiento, actividad.entrenamiento):
                if detalle is not None:
                    db.delete(detalle)
            db.delete(actividad)
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            raise

    @staticmethod
    def crear_tomas(
        db: Session,
        id_dieta: int,
        id_animal: int,
        horarios: list[tuple[date, time]],
        id_usuario: int,
    ) -> None:
        """Crea varias tomas de una dieta con un solo guardado (en lugar de uno por toma)."""
        try:
            db.add_all(
                [
                    ActividadModel(
                        tipo_actividad="alimentacion",
                        id_animal=id_animal,
                        fecha_programada=fecha,
                        hora_programada=hora,
                        duracion_horas=0,
                        duracion_minutos=0,
                        id_usuario_programo=id_usuario,
                        completada=False,
                        observaciones=None,
                        id_usuario_completo=None,
                        fecha_completada=None,
                        alimentacion=ActividadAlimentacionModel(id_dieta=id_dieta),
                    )
                    for fecha, hora in horarios
                ]
            )
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            raise

    @staticmethod
    def listar_tomas_rango(
        db: Session,
        id_dieta: int,
        fecha_desde: date,
        fecha_hasta: date,
    ) -> list[ActividadModel]:
        """Todas las tomas de una dieta en el rango, en una sola consulta.

        Evita consultar toma por toma: con la base remota cada ida y vuelta cuesta
        ~200 ms (más las cargas de relaciones) y la renovación excedía el tiempo
        de espera del gateway.
        """
        return (
            db.query(ActividadModel)
            .join(
                ActividadAlimentacionModel,
                ActividadAlimentacionModel.id_actividad == ActividadModel.id_actividad,
            )
            .filter(
                ActividadAlimentacionModel.id_dieta == id_dieta,
                ActividadModel.fecha_programada >= fecha_desde,
                ActividadModel.fecha_programada <= fecha_hasta,
            )
            .all()
        )

    @staticmethod
    def obtener_actividad_tratamiento(
        db: Session,
        id_tratamiento: int,
        fecha: date,
        hora: time,
    ) -> ActividadModel | None:
        return (
            db.query(ActividadModel)
            .join(
                ActividadTratamientoModel,
                ActividadTratamientoModel.id_actividad == ActividadModel.id_actividad,
            )
            .filter(
                ActividadTratamientoModel.id_tratamiento == id_tratamiento,
                ActividadTratamientoModel.fecha_programada == fecha,
                ActividadTratamientoModel.hora_programada == hora,
            )
            .first()
        )

    @staticmethod
    def obtener_actividades_tratamiento(
        db: Session,
        id_tratamiento: int,
    ) -> list[ActividadModel]:
        return (
            db.query(ActividadModel)
            .join(
                ActividadTratamientoModel,
                ActividadTratamientoModel.id_actividad == ActividadModel.id_actividad,
            )
            .filter(ActividadTratamientoModel.id_tratamiento == id_tratamiento)
            .all()
        )

    @staticmethod
    def eliminar_actividad_tratamiento(db: Session, actividad: ActividadModel) -> None:
        try:
            db.delete(actividad.tratamiento)
            db.delete(actividad)
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            raise

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
        "id_tratamiento": None,
        "descripcion_tratamiento": None,
        "medicamentos_tratamiento": [],
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
    if actividad.tratamiento is not None:
        resultado["id_tratamiento"] = actividad.tratamiento.id_tratamiento
        resultado["descripcion_tratamiento"] = actividad.tratamiento.descripcion_tratamiento
        resultado["medicamentos_tratamiento"] = medicamentos_de_texto(
            actividad.tratamiento.medicamentos_texto
        )
    return resultado
