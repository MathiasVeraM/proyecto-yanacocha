import httpx
from fastapi import APIRouter, Depends, Request
from src.config import GESTION_ANIMAL_SERVICE_URL
from src.proxy import METODOS_PERMITIDOS, get_http_client, reenviar
from src.seguridad import verificar_acceso

PREFIJO = "/api/animales"

router = APIRouter(
    prefix=PREFIJO,
    tags=["Gateway - Gestión Animal"],
    dependencies=[Depends(verificar_acceso)],
)

URL_DESTINO = f"{GESTION_ANIMAL_SERVICE_URL}{PREFIJO}"

# El listado y el registro de animales están en la raíz del prefijo, sin barra final.
# Con la ruta genérica se reenviaría a ".../api/animales/" y el servicio respondería con una redirección.
@router.api_route("", methods=METODOS_PERMITIDOS)
async def proxy_gestion_animal_raiz(
    request: Request,
    cliente: httpx.AsyncClient = Depends(get_http_client),
):
    return await reenviar(request, cliente, GESTION_ANIMAL_SERVICE_URL, PREFIJO.lstrip("/"), "gestión animal")

@router.api_route("/{path:path}", methods=METODOS_PERMITIDOS)
async def proxy_gestion_animal(
    path: str,
    request: Request,
    cliente: httpx.AsyncClient = Depends(get_http_client),
):
    return await reenviar(request, cliente, URL_DESTINO, path, "gestión animal")
