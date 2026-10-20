# Validación del token y control de acceso por módulo antes de reenviar una petición.
import jwt
from fastapi import HTTPException, Request, status
from src.config import ALGORITHM, SECRET_KEY
from src.mapa_rutas import NIVEL_PUBLICA, NIVEL_TOKEN, resolver_regla

# Este rol accede a todos los módulos sin necesitar que estén listados en su token
ID_ROL_ADMIN = 1

def _no_autenticado(detalle: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detalle,
        headers={"WWW-Authenticate": "Bearer"},
    )

def decodificar_token(token: str) -> dict:
    # Valida firma, expiración y que el token identifique a un usuario.
    try:
        payload = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM], options={"require": ["exp"]}
        )
    except jwt.PyJWTError:
        raise _no_autenticado("No se pudieron validar las credenciales o el token ha expirado")
    if payload.get("sub") is None:
        raise _no_autenticado("No se pudieron validar las credenciales o el token ha expirado")
    return payload

def tiene_acceso(payload: dict, codigo_servicio: str) -> bool:
    if payload.get("id_rol") == ID_ROL_ADMIN:
        return True
    modulos = payload.get("modulos")
    # Debe ser una lista: un string coincidiría por subcadena con el código
    return isinstance(modulos, list) and codigo_servicio in modulos

def _extraer_token(request: Request) -> str:
    esquema, _, token = request.headers.get("Authorization", "").partition(" ")
    if esquema.lower() != "bearer" or not token.strip():
        raise _no_autenticado("Falta el token de autenticación")
    return token.strip()

def verificar_acceso(request: Request) -> None:
    # Decide si la petición puede reenviarse al servicio.
    regla = resolver_regla(request.method, request.url.path)

    # Una ruta que no está en el mapa no se deja pasar
    if regla is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ruta no permitida")
    if regla.nivel == NIVEL_PUBLICA:
        return

    payload = decodificar_token(_extraer_token(request))
    if regla.nivel == NIVEL_TOKEN:
        return

    if not tiene_acceso(payload, regla.codigo_servicio):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para acceder a este módulo",
        )
