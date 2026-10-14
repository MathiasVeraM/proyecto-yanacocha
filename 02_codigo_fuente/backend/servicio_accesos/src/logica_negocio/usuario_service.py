from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.repositorios.usuario_repo import UsuarioRepository
from src.repositorios.rol_modulo_repo import RolModuloRepository
from src.logica_negocio.auth import hash_password

class UsuarioService:
    @staticmethod
    def _validar_rol_existe(db: Session, id_rol: int):
        if not RolModuloRepository.obtener_rol_por_id(db, id_rol):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El rol indicado no existe"
            )

    @staticmethod
    def listar_usuarios(db: Session):
        return UsuarioRepository.obtener_todos(db)

    @staticmethod
    def crear_nuevo_usuario(db: Session, usuario_in):
        usuario_existente = UsuarioRepository.obtener_por_correo(db, usuario_in.correo)
        if usuario_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El correo ya está registrado"
            )
        UsuarioService._validar_rol_existe(db, usuario_in.id_rol)

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

        # Los campos enviados como null se ignoran: ninguna columna acepta valores nulos
        update_data = {
            campo: valor
            for campo, valor in usuario_in.model_dump(exclude_unset=True).items()
            if valor is not None
        }

        correo = update_data.get("correo")
        if correo and correo != db_usuario.correo:
            otro_usuario = UsuarioRepository.obtener_por_correo(db, correo)
            if otro_usuario and otro_usuario.id_usuario != id_usuario:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El correo ya está registrado"
                )

        if "id_rol" in update_data:
            UsuarioService._validar_rol_existe(db, update_data["id_rol"])

        if "password" in update_data:
            update_data["password_hash"] = hash_password(update_data.pop("password"))

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
