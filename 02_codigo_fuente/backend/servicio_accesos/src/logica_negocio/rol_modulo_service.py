from sqlalchemy.orm import Session
from src.repositorios.rol_modulo_repo import RolModuloRepository

class RolModuloService:
    @staticmethod
    def listar_roles(db: Session):
        return RolModuloRepository.obtener_roles(db)

    @staticmethod
    def crear_rol(db: Session, rol_in):
        return RolModuloRepository.crear_rol(db, rol_in.dict())

    @staticmethod
    def listar_modulos(db: Session):
        return RolModuloRepository.obtener_modulos(db)

    @staticmethod
    def crear_modulo(db: Session, modulo_in):
        return RolModuloRepository.crear_modulo(db, modulo_in.dict())