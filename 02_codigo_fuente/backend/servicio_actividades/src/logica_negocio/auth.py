import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from src.config import ALGORITHM, SECRET_KEY

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
