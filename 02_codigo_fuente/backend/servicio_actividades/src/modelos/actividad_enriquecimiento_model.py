from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from src.config import DB_SCHEMA
from src.database import Base


class ActividadEnriquecimientoModel(Base):
    __tablename__ = "actividad_enriquecimiento"
    __table_args__ = (
        CheckConstraint(
            "tipo_enriquecimiento IN ('social', 'sensorial', 'alimenticio', 'cognitivo')",
            name="ck_actividad_enriquecimiento_tipo",
        ),
        {"schema": DB_SCHEMA},
    )

    id_actividad = Column(
        Integer,
        ForeignKey(f"{DB_SCHEMA}.actividad.id_actividad", ondelete="RESTRICT"),
        primary_key=True,
    )
    tipo_enriquecimiento = Column(String(20), nullable=False)
    descripcion_estimulo = Column(Text, nullable=False)

    actividad = relationship("ActividadModel", back_populates="enriquecimiento")
