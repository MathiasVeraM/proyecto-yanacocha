from datetime import date, datetime
from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, String, Text, TIMESTAMP, false
from sqlalchemy.sql import func
from src.config import DB_SCHEMA, ZONA_HORARIA
from src.database import Base

# Python pone la fecha en hora de Ecuador; el server_default de la base (UTC) queda solo como respaldo
def hoy_local() -> date:
    return datetime.now(ZONA_HORARIA).date()

def ahora_local() -> datetime:
    return datetime.now(ZONA_HORARIA).replace(tzinfo=None)

class AnimalModel(Base):
    __tablename__ = "animal"
    __table_args__ = {"schema": DB_SCHEMA}
    id_animal = Column(Integer, primary_key=True, index=True, autoincrement=True)
    codigo_animal = Column(String(30), unique=True, nullable=False)
    nombre_comun = Column(String(100), nullable=False)
    especie = Column(String(150))
    genero = Column(String(100))  # género taxonómico, no sexo
    familia = Column(String(100))
    edad_aproximada = Column(String(50))
    sexo = Column(String(15))
    estado_actual = Column(String(30), nullable=False, server_default="en_centro")
    fecha_ingreso = Column(Date, nullable=False, default=hoy_local, server_default=func.current_date())
    url_imagen = Column(String(500))

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
