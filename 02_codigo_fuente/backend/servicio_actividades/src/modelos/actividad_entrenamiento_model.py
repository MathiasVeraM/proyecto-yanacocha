from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from src.config import DB_SCHEMA
from src.database import Base


class ActividadEntrenamientoModel(Base):
    __tablename__ = "actividad_entrenamiento"
    __table_args__ = {"schema": DB_SCHEMA}

    id_actividad = Column(
        Integer,
        ForeignKey(f"{DB_SCHEMA}.actividad.id_actividad", ondelete="RESTRICT"),
        primary_key=True,
    )
    objetivo_entrenamiento = Column(Text, nullable=False)
    tipo_refuerzo = Column(String(150), nullable=False)

    actividad = relationship("ActividadModel", back_populates="entrenamiento")
