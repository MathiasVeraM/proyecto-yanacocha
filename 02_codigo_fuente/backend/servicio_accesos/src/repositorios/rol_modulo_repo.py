from sqlalchemy.orm import Session
from src.modelos.rol_modulo_model import RolModel, ModuloModel, RolPermisoModel
from src.modelos.usuario_model import UsuarioModel

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
    def actualizar_rol(db: Session, rol: RolModel, datos: dict):
        for campo, valor in datos.items():
            setattr(rol, campo, valor)
        db.commit()
        db.refresh(rol)
        return rol

    @staticmethod
    def eliminar_rol(db: Session, rol: RolModel):
        db.delete(rol)
        db.commit()

    @staticmethod
    def contar_usuarios_por_rol(db: Session, id_rol: int):
        return db.query(UsuarioModel).filter(UsuarioModel.id_rol == id_rol).count()

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

    @staticmethod
    def obtener_modulo_por_id(db: Session, id_modulo: int):
        return db.query(ModuloModel).filter(ModuloModel.id_modulo == id_modulo).first()

    @staticmethod
    def actualizar_modulo(db: Session, modulo: ModuloModel, datos: dict):
        for campo, valor in datos.items():
            setattr(modulo, campo, valor)
        db.commit()
        db.refresh(modulo)
        return modulo

    @staticmethod
    def eliminar_modulo(db: Session, modulo: ModuloModel):
        db.delete(modulo)
        db.commit()

    @staticmethod
    def obtener_permisos(db: Session):
        return db.query(RolPermisoModel).all()

    @staticmethod
    def existe_permiso(db: Session, id_rol: int, id_modulo: int):
        return db.query(RolPermisoModel).filter(
            RolPermisoModel.id_rol == id_rol, RolPermisoModel.id_modulo == id_modulo
        ).first() is not None

    @staticmethod
    def asignar_permiso(db: Session, id_rol: int, id_modulo: int):
        permiso = RolPermisoModel(id_rol=id_rol, id_modulo=id_modulo)
        db.add(permiso)
        db.commit()
        return permiso

    @staticmethod
    def quitar_permiso(db: Session, id_rol: int, id_modulo: int):
        db.query(RolPermisoModel).filter(
            RolPermisoModel.id_rol == id_rol, RolPermisoModel.id_modulo == id_modulo
        ).delete()
        db.commit()

    @staticmethod
    def eliminar_permisos_de_rol(db: Session, id_rol: int):
        db.query(RolPermisoModel).filter(RolPermisoModel.id_rol == id_rol).delete()
        db.commit()

    @staticmethod
    def eliminar_permisos_de_modulo(db: Session, id_modulo: int):
        db.query(RolPermisoModel).filter(RolPermisoModel.id_modulo == id_modulo).delete()
        db.commit()
