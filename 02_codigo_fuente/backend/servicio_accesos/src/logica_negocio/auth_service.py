from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.repositorios.rol_modulo_repo import RolModuloRepository
from src.repositorios.usuario_repo import UsuarioRepository
from src.logica_negocio.auth import verify_password, create_access_token

class AuthService:
    @staticmethod
    def iniciar_sesion(db: Session, correo: str, password: str) -> str:
        usuario = UsuarioRepository.obtener_por_correo(db, correo)
        if not usuario or not verify_password(password, usuario.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Correo o contraseña incorrectos"
            )

        # Se revisa después de validar la contraseña para no revelar qué correos existen
        if not usuario.activo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="La cuenta está desactivada. Contacta al administrador."
            )

        return create_access_token({
            "sub": usuario.correo,
            "id_usuario": usuario.id_usuario,
            "id_rol": usuario.id_rol,
            # Servicios a los que su rol tiene acceso; el gateway los lee de aquí
            "modulos": RolModuloRepository.obtener_codigos_servicio_por_rol(db, usuario.id_rol),
        })
