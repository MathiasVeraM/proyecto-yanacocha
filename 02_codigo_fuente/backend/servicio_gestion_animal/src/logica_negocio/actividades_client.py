import httpx2
from fastapi import HTTPException, status

from src.config import ACTIVIDADES_SERVICE_URL


def generar_actividades_tratamiento(id_tratamiento: int, autorizacion: str) -> list[dict]:
    url = (
        f"{ACTIVIDADES_SERVICE_URL}/api/actividades/tratamientos/"
        f"{id_tratamiento}/generar"
    )
    try:
        with httpx2.Client(timeout=5) as cliente:
            respuesta = cliente.post(url, headers={"Authorization": autorizacion})
            respuesta.raise_for_status()
            actividades = respuesta.json()
    except httpx2.TimeoutException as error:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="El servicio de actividades no respondió a tiempo",
        ) from error
    except httpx2.HTTPStatusError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "El servicio de actividades rechazó la generación "
                f"(HTTP {error.response.status_code})"
            ),
        ) from error
    except httpx2.HTTPError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo contactar al servicio de actividades",
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="El servicio de actividades devolvió una respuesta inválida",
        ) from error

    if not isinstance(actividades, list):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="El servicio de actividades devolvió una respuesta inválida",
        )
    return actividades
