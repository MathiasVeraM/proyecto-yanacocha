from sqlalchemy import Column, Date, ForeignKey, Index, Integer, Time
from sqlalchemy.orm import relationship

from src.config import DB_SCHEMA
from src.database import Base


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

    actividad = relationship("ActividadModel", back_populates="tratamiento")
