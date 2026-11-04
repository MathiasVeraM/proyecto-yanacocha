from sqlalchemy import Boolean, CheckConstraint, Column, Date, ForeignKey, Index, Integer, String, Text, TIMESTAMP, false, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.config import DB_SCHEMA
from src.database import Base
from src.modelos.fechas import ahora_local, hoy_local


class DietaModel(Base):
    __tablename__ = "dieta"
    __table_args__ = (
        CheckConstraint("frecuencia_valor > 0", name="ck_dieta_frecuencia_valor"),
        CheckConstraint(
            "frecuencia_unidad IN ('horas', 'dias', 'semanas')",
            name="ck_dieta_frecuencia_unidad",
        ),
        CheckConstraint(
            "fecha_fin IS NULL OR fecha_fin >= fecha_inicio",
            name="ck_dieta_fechas",
        ),
        Index(
            "ix_dieta_id_animal_vigente",
            "id_animal",
            unique=True,
            postgresql_where=text("vigente"),
            sqlite_where=text("vigente = 1"),
        ),
        Index("ix_dieta_id_usuario_creador", "id_usuario_creador"),
        {"schema": DB_SCHEMA},
    )

    id_dieta = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_animal = Column(
        Integer,
        ForeignKey("gestion_animal.animal.id_animal", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    id_usuario_creador = Column(
        Integer,
        ForeignKey("public.usuario.id_usuario", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    fecha_inicio = Column(Date, nullable=False, default=hoy_local, server_default=func.current_date())
    fecha_fin = Column(Date)
    frecuencia_valor = Column(Integer, nullable=False)
    frecuencia_unidad = Column(String(10), nullable=False)
    vigente = Column(Boolean, nullable=False, default=True, server_default=false())
    observaciones = Column(Text)
    fecha_registro = Column(
        TIMESTAMP,
        nullable=False,
        default=ahora_local,
        server_default=func.now(),
    )

    alimentos = relationship("DietaAlimentoModel", back_populates="dieta", lazy="selectin")
