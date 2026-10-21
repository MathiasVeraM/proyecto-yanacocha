import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from src.config import ALGORITHM, CODIGO_MODULO, ID_ROL_ADMIN, SECRET_KEY

# El token lo emite el servicio de accesos; aquí solo se valida
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
    # El id_usuario se usa para saber quién registra cada diagnóstico
    if payload.get("sub") is None or not isinstance(payload.get("id_usuario"), int):
        raise credentials_exception
    return payload

def verificar_acceso_modulo(payload: dict = Depends(verificar_token_access)) -> dict:
    # El gateway ya revisa el permiso; se repite aquí por si alguien llama al servicio directamente
    modulos = payload.get("modulos")
    tiene_permiso = isinstance(modulos, list) and CODIGO_MODULO in modulos
    if payload.get("id_rol") != ID_ROL_ADMIN and not tiene_permiso:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para acceder a este módulo",
        )
    return payload
