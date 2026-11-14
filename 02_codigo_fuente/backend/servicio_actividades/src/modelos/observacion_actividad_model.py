from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
    TIMESTAMP,
    false,
)
from sqlalchemy.sql import func

from src.config import DB_SCHEMA
from src.database import Base
from src.modelos.fechas import ahora_local


class ObservacionActividadModel(Base):
    __tablename__ = "observacion_actividad"
    __table_args__ = (
        CheckConstraint(
            "categoria IN ('recinto', 'comportamiento', 'estado_fisico')",
            name="ck_observacion_actividad_categoria",
        ),
        CheckConstraint(
            "severidad IN ('bajo', 'medio', 'alto')",
            name="ck_observacion_actividad_severidad",
        ),
        {"schema": DB_SCHEMA},
    )

    id_observacion = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_actividad = Column(
        Integer,
        ForeignKey(f"{DB_SCHEMA}.actividad.id_actividad", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    categoria = Column(String(20), nullable=False)
    severidad = Column(String(10), nullable=False)
    detalle = Column(Text, nullable=False)
    genera_alerta = Column(Boolean, nullable=False, default=False, server_default=false())
    id_usuario = Column(Integer, nullable=False)
    fecha_registro = Column(
        TIMESTAMP,
        nullable=False,
        default=ahora_local,
        server_default=func.now(),
    )
