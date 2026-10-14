from sqlalchemy import Column, ForeignKey, Integer, String
from src.database import Base

class RolModel(Base):
    __tablename__ = "rol"
    id_rol = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre_rol = Column(String(50), unique=True, nullable=False)
    descripcion = Column(String)

class ModuloModel(Base):
    __tablename__ = "modulo"
    id_modulo = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre_modulo = Column(String(100), unique=True, nullable=False)
    codigo_servicio = Column(String(50), nullable=False)


class RolPermisoModel(Base):
    __tablename__ = "rol_permiso"
    id_rol = Column(Integer, ForeignKey("rol.id_rol", ondelete="CASCADE"), primary_key=True)
    id_modulo = Column(Integer, ForeignKey("modulo.id_modulo", ondelete="CASCADE"), primary_key=True)
