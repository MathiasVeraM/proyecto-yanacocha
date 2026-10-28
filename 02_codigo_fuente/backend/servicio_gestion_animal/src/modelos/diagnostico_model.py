from sqlalchemy import Boolean, Column, ForeignKey, Integer, Text, TIMESTAMP, false
from sqlalchemy.sql import func

from src.config import DB_SCHEMA
from src.database import Base
from src.modelos.fechas import ahora_local


class DiagnosticoModel(Base):
    __tablename__ = "diagnostico"
    __table_args__ = {"schema": DB_SCHEMA}

    id_diagnostico = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_animal = Column(Integer, ForeignKey(f"{DB_SCHEMA}.animal.id_animal"), nullable=False, index=True)
    # La FK a public.usuario existe en la base de datos; aquí no se declara porque
    # la tabla usuario pertenece al servicio de accesos
    id_usuario = Column(Integer, nullable=False, index=True)
    diagnostico = Column(Text, nullable=False)
    observaciones = Column(Text)
    es_critico = Column(Boolean, nullable=False, server_default=false())
    fecha_registro = Column(TIMESTAMP, nullable=False, default=ahora_local, server_default=func.now())
