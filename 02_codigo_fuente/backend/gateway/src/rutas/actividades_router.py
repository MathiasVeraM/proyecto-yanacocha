import httpx
from fastapi import APIRouter, Depends, Request

from src.config import ACTIVIDADES_SERVICE_URL
from src.proxy import METODOS_PERMITIDOS, get_http_client, reenviar
from src.seguridad import verificar_acceso

PREFIJO = "/api/actividades"

router = APIRouter(
    prefix=PREFIJO,
    tags=["Gateway - Actividades"],
    dependencies=[Depends(verificar_acceso)],
)

URL_DESTINO = f"{ACTIVIDADES_SERVICE_URL}{PREFIJO}"


@router.api_route("", methods=METODOS_PERMITIDOS)
async def proxy_actividades_raiz(
    request: Request,
    cliente: httpx.AsyncClient = Depends(get_http_client),
):
    return await reenviar(
        request,
        cliente,
        ACTIVIDADES_SERVICE_URL,
        PREFIJO.lstrip("/"),
        "actividades",
    )


@router.api_route("/{path:path}", methods=METODOS_PERMITIDOS)
async def proxy_actividades(
    path: str,
    request: Request,
    cliente: httpx.AsyncClient = Depends(get_http_client),
):
    return await reenviar(
        request,
        cliente,
        URL_DESTINO,
        path,
        "actividades",
    )
