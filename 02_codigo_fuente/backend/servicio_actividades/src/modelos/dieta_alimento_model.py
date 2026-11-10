from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from src.config import DB_SCHEMA
from src.database import Base


class DietaAlimentoModel(Base):
    __tablename__ = "dieta_alimento"
    __table_args__ = (
        CheckConstraint("cantidad_gramos > 0", name="ck_dieta_alimento_cantidad"),
        {"schema": DB_SCHEMA},
    )

    id_dieta_alimento = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_dieta = Column(
        Integer,
        ForeignKey(f"{DB_SCHEMA}.dieta.id_dieta", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    nombre_alimento = Column(String(150), nullable=False)
    cantidad_gramos = Column(Numeric(8, 2), nullable=False)

    dieta = relationship("DietaModel", back_populates="alimentos")
