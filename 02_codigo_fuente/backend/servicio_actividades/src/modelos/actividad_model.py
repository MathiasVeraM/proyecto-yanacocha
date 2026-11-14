from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    Time,
    TIMESTAMP,
    false,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.config import DB_SCHEMA
from src.database import Base
from src.modelos.fechas import ahora_local, hoy_local


class ActividadModel(Base):
    __tablename__ = "actividad"
    __table_args__ = (
        CheckConstraint(
            "tipo_actividad IN ('alimentacion', 'enriquecimiento', 'entrenamiento', 'limpieza', 'tratamiento')",
            name="ck_actividad_tipo",
        ),
        CheckConstraint("duracion_horas >= 0", name="ck_actividad_duracion_horas"),
        CheckConstraint(
            "duracion_minutos BETWEEN 0 AND 59",
            name="ck_actividad_duracion_minutos",
        ),
        CheckConstraint(
            """
            (
                tipo_actividad = 'limpieza'
                AND id_recinto IS NOT NULL
                AND id_animal IS NULL
                AND (duracion_horas * 60 + duracion_minutos) > 0
            )
            OR
            (
                tipo_actividad IN (
                    'alimentacion',
                    'enriquecimiento',
                    'entrenamiento',
                    'tratamiento'
                )
                AND id_animal IS NOT NULL
            )
            """,
            name="ck_actividad_tipo_destino",
        ),
        CheckConstraint(
            "tipo_actividad <> 'entrenamiento' OR (duracion_horas * 60 + duracion_minutos) > 0",
            name="ck_actividad_entrenamiento_duracion",
        ),
        CheckConstraint(
            "NOT completada OR (id_usuario_completo IS NOT NULL AND fecha_completada IS NOT NULL)",
            name="ck_actividad_completada",
        ),
        {"schema": DB_SCHEMA},
    )

    id_actividad = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tipo_actividad = Column(String(20), nullable=False)
    id_animal = Column(
        Integer,
        ForeignKey("gestion_animal.animal.id_animal", ondelete="RESTRICT"),
        index=True,
    )
    id_recinto = Column(
        Integer,
        ForeignKey("gestion_animal.recinto.id_recinto", ondelete="RESTRICT"),
        index=True,
    )
    fecha_programada = Column(Date, nullable=False, default=hoy_local, index=True)
    hora_programada = Column(Time)
    duracion_horas = Column(SmallInteger, nullable=False, default=0, server_default="0")
    duracion_minutos = Column(SmallInteger, nullable=False, default=0, server_default="0")
    id_usuario_programo = Column(
        Integer,
        ForeignKey("public.usuario.id_usuario", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    fecha_registro = Column(
        TIMESTAMP,
        nullable=False,
        default=ahora_local,
        server_default=func.now(),
    )
    completada = Column(Boolean, nullable=False, default=False, server_default=false())
    observaciones = Column(Text)
    id_usuario_completo = Column(
        Integer,
        ForeignKey("public.usuario.id_usuario", ondelete="RESTRICT"),
        index=True,
    )
    fecha_completada = Column(TIMESTAMP)

    # Detalle según el tipo (uno a uno). actividad_a_dict los lee para armar la respuesta, así
    # que se cargan en la misma consulta que la actividad (LEFT JOIN): con "selectin" cada
    # listado hacía 4 consultas extra a la base remota.
    alimentacion = relationship(
        "ActividadAlimentacionModel",
        back_populates="actividad",
        uselist=False,
        lazy="joined",
    )
    enriquecimiento = relationship(
        "ActividadEnriquecimientoModel",
        back_populates="actividad",
        uselist=False,
        lazy="joined",
    )
    entrenamiento = relationship(
        "ActividadEntrenamientoModel",
        back_populates="actividad",
        uselist=False,
        lazy="joined",
    )
    tratamiento = relationship(
        "ActividadTratamientoModel",
        back_populates="actividad",
        uselist=False,
        lazy="joined",
    )
