from sqlalchemy.orm import Session
from src.modelos.usuario_model import RolModel, ModuloModel

class RolModuloRepository:
    @staticmethod
    def obtener_roles(db: Session):
        return db.query(RolModel).all()

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
    def crear_modulo(db: Session, modulo_data: dict):
        modulo = ModuloModel(**modulo_data)
        db.add(modulo)
        db.commit()
        db.refresh(modulo)
        return modulo