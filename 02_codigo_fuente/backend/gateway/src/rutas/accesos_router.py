import httpx
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from src.config import ACCESSOS_SERVICE_URL

router = APIRouter(prefix="/api/auth", tags=["Gateway - Accesos"])
http_client = httpx.AsyncClient()

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_accesos(path: str, request: Request):
    url = f"{ACCESSOS_SERVICE_URL}/api/auth/{path}"
    
    # Copiamos headers y cuerpo de la petición original
    headers = dict(request.headers)
    headers.pop("host", None)
    body = await request.body()
    
    try:
        response = await http_client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=body,
            params=request.query_params
        )
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    except httpx.RequestError:
        return JSONResponse(
            status_code=503,
            content={"detail": "El servicio de accesos no está disponible"}
        )