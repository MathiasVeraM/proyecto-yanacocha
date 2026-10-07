from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.repositorios.usuario_repo import UsuarioRepository
from src.logica_negocio.auth import hash_password

class UsuarioService:
    @staticmethod
    def crear_nuevo_usuario(db: Session, usuario_in):
        usuario_existente = UsuarioRepository.obtener_por_correo(db, usuario_in.correo)
        if usuario_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El correo ya está registrado"
            )
        
        hashed_pass = hash_password(usuario_in.password)
        datos_usuario = {
            "nombre": usuario_in.nombre,
            "apellido": usuario_in.apellido,
            "correo": usuario_in.correo,
            "password_hash": hashed_pass,
            "id_rol": usuario_in.id_rol
        }
        return UsuarioRepository.crear_usuario(db, datos_usuario)

    @staticmethod
    def actualizar_datos_usuario(db: Session, id_usuario: int, usuario_in):
        db_usuario = UsuarioRepository.obtener_por_id(db, id_usuario)
        if not db_usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        update_data = usuario_in.dict(exclude_unset=True)
        if "password" in update_data and update_data["password"]:
            password_plano = update_data.pop("password")
            update_data["password_hash"] = hash_password(password_plano)
        else:
            update_data.pop("password", None)

        return UsuarioRepository.actualizar_usuario(db, db_usuario, update_data)

    @staticmethod
    def desactivar_usuario(db: Session, id_usuario: int):
        db_usuario = UsuarioRepository.obtener_por_id(db, id_usuario)
        if not db_usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        return UsuarioRepository.actualizar_usuario(db, db_usuario, {"activo": False})