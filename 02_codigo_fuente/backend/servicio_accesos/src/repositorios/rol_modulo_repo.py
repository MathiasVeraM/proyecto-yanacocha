from sqlalchemy.orm import Session
from src.modelos.rol_modulo_model import RolModel, ModuloModel

class RolModuloRepository:
    @staticmethod
    def obtener_roles(db: Session):
        return db.query(RolModel).all()

    @staticmethod
    def obtener_rol_por_id(db: Session, id_rol: int):
        return db.query(RolModel).filter(RolModel.id_rol == id_rol).first()

    @staticmethod
    def obtener_rol_por_nombre(db: Session, nombre_rol: str):
        return db.query(RolModel).filter(RolModel.nombre_rol == nombre_rol).first()

    @staticmethod
    def crear_rol(db: Session, rol_data: dict):
        rol = RolModel(**rol_data)
        db.add(rol)
        db.commit()
        db.refresh(rol)
        return rol

    @staticmethod
    def obtener_modulos(db: Session):
        return db.query(ModuloModel).all()

    @staticmethod
    def obtener_modulo_por_nombre(db: Session, nombre_modulo: str):
        return db.query(ModuloModel).filter(ModuloModel.nombre_modulo == nombre_modulo).first()

    @staticmethod
    def crear_modulo(db: Session, modulo_data: dict):
        modulo = ModuloModel(**modulo_data)
        db.add(modulo)
        db.commit()
        db.refresh(modulo)
        return modulo
