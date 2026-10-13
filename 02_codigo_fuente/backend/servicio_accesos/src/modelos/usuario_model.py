from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
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

class UsuarioModel(Base):
    __tablename__ = "usuario"
    id_usuario = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    correo = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    id_rol = Column(Integer, ForeignKey("rol.id_rol"), nullable=False)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(TIMESTAMP, server_default=func.now())