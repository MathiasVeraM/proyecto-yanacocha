from sqlalchemy.orm import Session
from src.modelos.usuario_model import UsuarioModel

class UsuarioRepository:
    @staticmethod
    def obtener_todos(db: Session):
        return db.query(UsuarioModel).all()
    
    @staticmethod
    def obtener_por_correo(db: Session, correo: str):
        return db.query(UsuarioModel).filter(UsuarioModel.correo == correo).first()

    @staticmethod
    def obtener_por_id(db: Session, id_usuario: int):
        return db.query(UsuarioModel).filter(UsuarioModel.id_usuario == id_usuario).first()

    @staticmethod
    def crear_usuario(db: Session, usuario_data: dict):
        db_usuario = UsuarioModel(**usuario_data)
        db.add(db_usuario)
        db.commit()
        db.refresh(db_usuario)
        return db_usuario

    @staticmethod
    def actualizar_usuario(db: Session, db_usuario: UsuarioModel, update_data: dict):
        for key, value in update_data.items():
            setattr(db_usuario, key, value)
        db.commit()
        db.refresh(db_usuario)
        return db_usuario