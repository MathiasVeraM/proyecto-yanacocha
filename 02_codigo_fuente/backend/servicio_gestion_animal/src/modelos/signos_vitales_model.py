from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
)
from sqlalchemy.orm import relationship

from src.config import DB_SCHEMA
from src.database import Base


class SignosVitalesModel(Base):
    __tablename__ = "signos_vitales"
    __table_args__ = (
        CheckConstraint("peso_kg IS NULL OR peso_kg > 0", name="ck_signos_vitales_peso_positivo"),
        CheckConstraint(
            "temperatura_c IS NULL OR temperatura_c BETWEEN 0 AND 60",
            name="ck_signos_vitales_temperatura_rango",
        ),
        CheckConstraint(
            "frecuencia_cardiaca_lpm IS NULL OR frecuencia_cardiaca_lpm > 0",
            name="ck_signos_vitales_fc_positiva",
        ),
        CheckConstraint(
            "frecuencia_respiratoria_rpm IS NULL OR frecuencia_respiratoria_rpm > 0",
            name="ck_signos_vitales_fr_positiva",
        ),
        CheckConstraint(
            "tiempo_llenado_capilar_s IS NULL OR tiempo_llenado_capilar_s > 0",
            name="ck_signos_vitales_tllc_positivo",
        ),
        CheckConstraint(
            "hidratacion IS NULL OR hidratacion IN "
            "('normal', 'deshidratacion_leve', 'deshidratacion_moderada', 'deshidratacion_severa')",
            name="ck_signos_vitales_hidratacion",
        ),
        CheckConstraint(
            "condicion_corporal IS NULL OR condicion_corporal BETWEEN 1 AND 5",
            name="ck_signos_vitales_condicion_corporal",
        ),
        CheckConstraint(
            "mucosas IS NULL OR mucosas IN "
            "('rosadas', 'palidas', 'cianoticas', 'ictericas', 'congestionadas')",
            name="ck_signos_vitales_mucosas",
        ),
        CheckConstraint(
            "actitud IS NULL OR actitud IN ('alerta', 'deprimido', 'estuporoso', 'agitado')",
            name="ck_signos_vitales_actitud",
        ),
        CheckConstraint(
            "peso_kg IS NOT NULL OR temperatura_c IS NOT NULL OR "
            "frecuencia_cardiaca_lpm IS NOT NULL OR frecuencia_respiratoria_rpm IS NOT NULL OR "
            "tiempo_llenado_capilar_s IS NOT NULL OR hidratacion IS NOT NULL OR "
            "condicion_corporal IS NOT NULL OR mucosas IS NOT NULL OR actitud IS NOT NULL",
            name="ck_signos_vitales_no_vacio",
        ),
        {"schema": DB_SCHEMA},
    )

    id_signos_vitales = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_diagnostico = Column(
        Integer,
        ForeignKey(f"{DB_SCHEMA}.diagnostico.id_diagnostico", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
        index=True,
    )
    peso_kg = Column(Numeric(8, 3))
    temperatura_c = Column(Numeric(4, 1))
    frecuencia_cardiaca_lpm = Column(Integer)
    frecuencia_respiratoria_rpm = Column(Integer)
    tiempo_llenado_capilar_s = Column(Numeric(4, 1))
    hidratacion = Column(String(30))
    condicion_corporal = Column(SmallInteger)
    mucosas = Column(String(20))
    actitud = Column(String(20))

    diagnostico = relationship("DiagnosticoModel", back_populates="signos_vitales")

    @property
    def fecha_diagnostico(self):
        return self.diagnostico.fecha_registro
