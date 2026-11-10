from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from src.config import DB_SCHEMA
from src.database import Base


class ActividadAlimentacionModel(Base):
    __tablename__ = "actividad_alimentacion"
    __table_args__ = {"schema": DB_SCHEMA}

    id_actividad = Column(
        Integer,
        ForeignKey(f"{DB_SCHEMA}.actividad.id_actividad", ondelete="RESTRICT"),
        primary_key=True,
    )
    id_dieta = Column(
        Integer,
        ForeignKey(f"{DB_SCHEMA}.dieta.id_dieta", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    actividad = relationship("ActividadModel", back_populates="alimentacion")
    dieta = relationship("DietaModel")
