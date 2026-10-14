import httpx
from fastapi import APIRouter, Depends, Request
from src.config import ACCESSOS_SERVICE_URL
from src.proxy import METODOS_PERMITIDOS, get_http_client, reenviar

router = APIRouter(prefix="/api/auth", tags=["Gateway - Accesos"])

URL_DESTINO = f"{ACCESSOS_SERVICE_URL}/api/auth"


@router.api_route("/{path:path}", methods=METODOS_PERMITIDOS)
async def proxy_accesos(
    path: str,
    request: Request,
    cliente: httpx.AsyncClient = Depends(get_http_client),
):
    return await reenviar(request, cliente, URL_DESTINO, path, "accesos")
