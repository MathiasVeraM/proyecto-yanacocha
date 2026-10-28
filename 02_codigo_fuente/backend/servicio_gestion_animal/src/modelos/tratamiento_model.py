from sqlalchemy import Column, Date, ForeignKey, Integer, String
from sqlalchemy.sql import func

from src.config import DB_SCHEMA
from src.database import Base
from src.modelos.fechas import hoy_local


class TratamientoModel(Base):
    __tablename__ = "tratamiento"
    __table_args__ = {"schema": DB_SCHEMA}

    id_tratamiento = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_diagnostico = Column(
        Integer, ForeignKey(f"{DB_SCHEMA}.diagnostico.id_diagnostico"), nullable=False, index=True
    )
    medicamento_o_proceso = Column(String(200), nullable=False)
    dosis = Column(String(100))
    frecuencia = Column(String(100))
    fecha_inicio = Column(Date, nullable=False, default=hoy_local, server_default=func.current_date())
    fecha_fin = Column(Date)
    estado = Column(String(20), nullable=False, server_default="en_curso")
