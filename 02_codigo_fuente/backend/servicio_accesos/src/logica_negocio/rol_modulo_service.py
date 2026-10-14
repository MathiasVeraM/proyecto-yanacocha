from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.repositorios.rol_modulo_repo import RolModuloRepository

class RolModuloService:
    @staticmethod
    def listar_roles(db: Session):
        return RolModuloRepository.obtener_roles(db)

    @staticmethod
    def crear_rol(db: Session, rol_in):
        if RolModuloRepository.obtener_rol_por_nombre(db, rol_in.nombre_rol):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un rol con ese nombre"
            )
        return RolModuloRepository.crear_rol(db, rol_in.model_dump())

    @staticmethod
    def listar_modulos(db: Session):
        return RolModuloRepository.obtener_modulos(db)

    @staticmethod
    def crear_modulo(db: Session, modulo_in):
        if RolModuloRepository.obtener_modulo_por_nombre(db, modulo_in.nombre_modulo):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un módulo con ese nombre"
            )
        return RolModuloRepository.crear_modulo(db, modulo_in.model_dump())
