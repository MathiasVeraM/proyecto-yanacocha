from sqlalchemy.orm import Session
from ..modelos.usuario_model import UsuarioModel

class UsuarioRepository:
    @staticmethod
    def obtener_por_correo(db: Session, correo: str):
        return db.query(UsuarioModel).filter(UsuarioModel.correo == correo).first()

    @staticmethod
    def crear_usuario(db: Session, usuario_data: dict):
        db_usuario = UsuarioModel(**usuario_data)
        db.add(db_usuario)
        db.commit()
        db.refresh(db_usuario)
        return db_usuario