from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Time,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.config import DB_SCHEMA
from src.database import Base
from src.modelos.fechas import hoy_local


class TratamientoModel(Base):
    __tablename__ = "tratamiento"
    __table_args__ = (
        CheckConstraint(
            "fecha_fin IS NULL OR fecha_fin >= fecha_inicio",
            name="ck_tratamiento_fechas",
        ),
        CheckConstraint(
            "frecuencia_valor IS NULL OR frecuencia_valor > 0",
            name="ck_tratamiento_frecuencia_valor",
        ),
        CheckConstraint(
            "frecuencia_unidad IS NULL OR frecuencia_unidad IN ('horas', 'dias')",
            name="ck_tratamiento_frecuencia_unidad",
        ),
        CheckConstraint(
            "(frecuencia_valor IS NULL) = (frecuencia_unidad IS NULL)",
            name="ck_tratamiento_frecuencia_completa",
        ),
        {"schema": DB_SCHEMA},
    )

    id_tratamiento = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_diagnostico = Column(
        Integer,
        ForeignKey(f"{DB_SCHEMA}.diagnostico.id_diagnostico", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    descripcion = Column(Text, nullable=False)
    medicamento_o_proceso = Column(String(200))
    dosis = Column(String(100))
    frecuencia = Column(String(100))
    fecha_inicio = Column(Date, nullable=False, default=hoy_local, server_default=func.current_date())
    fecha_fin = Column(Date)
    frecuencia_valor = Column(Integer)
    frecuencia_unidad = Column(String(10))
    hora_inicio = Column(Time)
    estado = Column(String(20), nullable=False, server_default="en_curso")

    medicamentos = relationship(
        "TratamientoMedicamentoModel",
        back_populates="tratamiento",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="TratamientoMedicamentoModel.id_tratamiento_medicamento",
    )


class TratamientoMedicamentoModel(Base):
    __tablename__ = "tratamiento_medicamento"
    __table_args__ = (
        Index(
            "ix_tratamiento_medicamento_id_tratamiento",
            "id_tratamiento",
        ),
        CheckConstraint("dosis_ml > 0", name="ck_tratamiento_medicamento_dosis"),
        {"schema": DB_SCHEMA},
    )

    id_tratamiento_medicamento = Column(Integer, primary_key=True, autoincrement=True)
    id_tratamiento = Column(
        Integer,
        ForeignKey(f"{DB_SCHEMA}.tratamiento.id_tratamiento", ondelete="RESTRICT"),
        nullable=False,
    )
    nombre_medicamento = Column(String(150), nullable=False)
    dosis_ml = Column(Numeric(8, 2), nullable=False)

    tratamiento = relationship("TratamientoModel", back_populates="medicamentos")
