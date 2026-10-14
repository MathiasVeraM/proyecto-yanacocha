import os
import sys
from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.logica_negocio.auth import hash_password
from src.repositorios.usuario_repo import UsuarioRepository

ID_ROL_ADMIN = 1  # Asegúrate de que el id 1 sea el rol Administrador en la BD
LONGITUD_MINIMA_PASSWORD = 8

def crear_admin(db: Session, correo: str, password: str) -> bool:
    """Crea el administrador inicial. Devuelve False si el correo ya existía."""
    if len(password) < LONGITUD_MINIMA_PASSWORD:
        raise ValueError(f"La contraseña debe tener al menos {LONGITUD_MINIMA_PASSWORD} caracteres")

    if UsuarioRepository.obtener_por_correo(db, correo):
        return False

    UsuarioRepository.crear_usuario(db, {
        "nombre": "Administrador",
        "apellido": "Sistema",
        "correo": correo,
        "password_hash": hash_password(password),
        "id_rol": ID_ROL_ADMIN,
        "activo": True,
    })
    return True

def main() -> int:
    correo = os.getenv("ADMIN_CORREO")
    password = os.getenv("ADMIN_PASSWORD")
    if not correo or not password:
        print("Define ADMIN_CORREO y ADMIN_PASSWORD en el archivo .env")
        return 1

    db = SessionLocal()
    try:
        creado = crear_admin(db, correo, password)
    except ValueError as error:
        print(error)
        return 1
    finally:
        db.close()

    if creado:
        print(f"¡Administrador creado con éxito! Correo: {correo}")
    else:
        print("El administrador ya existe en la base de datos.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
