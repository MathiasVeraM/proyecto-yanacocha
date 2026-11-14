from sqlalchemy import Column, Date, ForeignKey, Index, Integer, Time, select
from sqlalchemy.orm import column_property, relationship

from src.config import DB_SCHEMA
from src.database import Base
from src.modelos import referencias_model  # noqa: F401  (registra gestion_animal.tratamiento)

_TRATAMIENTO = Base.metadata.tables["gestion_animal.tratamiento"]


class ActividadTratamientoModel(Base):
    __tablename__ = "actividad_tratamiento"
    __table_args__ = (
        Index(
            "ix_actividad_tratamiento_programacion",
            "id_tratamiento",
            "fecha_programada",
            "hora_programada",
            unique=True,
        ),
        {"schema": DB_SCHEMA},
    )

    id_actividad = Column(
        Integer,
        ForeignKey(f"{DB_SCHEMA}.actividad.id_actividad", ondelete="RESTRICT"),
        primary_key=True,
    )
    id_tratamiento = Column(
        Integer,
        ForeignKey("gestion_animal.tratamiento.id_tratamiento", ondelete="RESTRICT"),
        nullable=False,
    )
    fecha_programada = Column(Date, nullable=False)
    hora_programada = Column(Time, nullable=False)

    # Qué se aplica en la dosis, para mostrarlo en el calendario y las tarjetas. Es una subconsulta
    # por clave primaria dentro de la misma consulta de la actividad (el detalle se carga con JOIN):
    # no agrega consultas ni peticiones al servicio de gestión animal.
    descripcion_tratamiento = column_property(
        select(_TRATAMIENTO.c.descripcion)
        .where(_TRATAMIENTO.c.id_tratamiento == id_tratamiento)
        .scalar_subquery()
    )

    actividad = relationship("ActividadModel", back_populates="tratamiento")
