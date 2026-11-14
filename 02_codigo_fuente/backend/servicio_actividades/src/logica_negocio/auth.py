import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from src.config import (
    ALGORITHM,
    ID_ROL_MANEJO_ANIMAL,
    ID_ROL_VETERINARIA,
    ID_ROL_VOLUNTARIO,
    SECRET_KEY,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def verificar_token_access(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales o el token ha expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"require": ["exp"]})
    except jwt.PyJWTError:
        raise credentials_exception
    if payload.get("sub") is None or not isinstance(payload.get("id_usuario"), int):
        raise credentials_exception
    return payload


def requiere_rol(*roles: int):
    """Dependencia que solo deja pasar a los roles indicados (el gateway también lo revisa).

    Las consultas no la usan: todos los roles con el módulo pueden ver la planificación.
    """
    permitidos = frozenset(roles)

    def _verificar(payload: dict = Depends(verificar_token_access)) -> dict:
        id_rol = payload.get("id_rol")
        # isinstance: un id_rol mal formado (ej. una lista) se rechaza en vez de fallar
        if not isinstance(id_rol, int) or id_rol not in permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tu rol no tiene permiso para realizar esta acción",
            )
        return payload

    return _verificar


# Crear, editar, eliminar y reabrir actividades, dietas y tomas
solo_manejo_animal = requiere_rol(ID_ROL_MANEJO_ANIMAL)
# Completar actividades y registrar observaciones
manejo_o_voluntario = requiere_rol(ID_ROL_MANEJO_ANIMAL, ID_ROL_VOLUNTARIO)
# Sincronizar las dosis al guardar un tratamiento (lo llama gestión animal con el token de Veterinaria)
veterinaria_o_manejo = requiere_rol(ID_ROL_VETERINARIA, ID_ROL_MANEJO_ANIMAL)
