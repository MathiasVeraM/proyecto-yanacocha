"""Lógica común para reenviar peticiones del gateway a cualquier microservicio."""
from urllib.parse import unquote

import httpx
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from src.config import PROXY_TIMEOUT_SECONDS

METODOS_PERMITIDOS = ["GET", "POST", "PUT", "PATCH", "DELETE"]

# Cabeceras que solo aplican a una conexión y no deben reenviarse (RFC 9110)
CABECERAS_HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}

# httpx recalcula host y content-length para la nueva petición
CABECERAS_EXCLUIDAS_PETICION = CABECERAS_HOP_BY_HOP | {"host", "content-length"}

# httpx ya descomprime el cuerpo, así que content-encoding y content-length dejarían de ser ciertos
CABECERAS_EXCLUIDAS_RESPUESTA = CABECERAS_HOP_BY_HOP | {"content-encoding", "content-length"}


def crear_cliente_http() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=PROXY_TIMEOUT_SECONDS)


def get_http_client(request: Request) -> httpx.AsyncClient:
    """Dependencia que entrega el cliente HTTP compartido creado en el lifespan de la app."""
    return request.app.state.http_client


def es_ruta_segura(path: str) -> bool:
    """Rechaza rutas con segmentos '..' (aunque vengan codificados) para no salir del prefijo del servicio."""
    decodificado = path
    # Decodificamos varias veces para atrapar dobles codificaciones como %252e%252e
    for _ in range(3):
        decodificado = unquote(decodificado)
    segmentos = decodificado.replace("\\", "/").split("/")
    return ".." not in segmentos


def filtrar_cabeceras(cabeceras: list[tuple[str, str]], excluidas: set[str]) -> list[tuple[str, str]]:
    return [(nombre, valor) for nombre, valor in cabeceras if nombre.lower() not in excluidas]


def construir_cabeceras_peticion(request: Request) -> list[tuple[str, str]]:
    cabeceras = filtrar_cabeceras(
        request.headers.items(),
        CABECERAS_EXCLUIDAS_PETICION | {"x-forwarded-for", "x-forwarded-proto"},
    )

    # Informamos al servicio la IP real del cliente y el protocolo original
    ip_cliente = request.client.host if request.client else "desconocido"
    reenviado_por = request.headers.get("x-forwarded-for")
    cabeceras.append(
        ("x-forwarded-for", f"{reenviado_por}, {ip_cliente}" if reenviado_por else ip_cliente)
    )
    cabeceras.append(("x-forwarded-proto", request.url.scheme))
    return cabeceras


async def reenviar(
    request: Request,
    cliente: httpx.AsyncClient,
    url_destino: str,
    path: str,
    nombre_servicio: str,
) -> Response:
    """Reenvía la petición a `url_destino/path` y devuelve la respuesta del servicio."""
    if not es_ruta_segura(path):
        return JSONResponse(status_code=400, content={"detail": "Ruta no permitida"})

    url = f"{url_destino.rstrip('/')}/{path}"
    if request.url.query:
        url = f"{url}?{request.url.query}"

    try:
        respuesta = await cliente.request(
            method=request.method,
            url=url,
            headers=construir_cabeceras_peticion(request),
            content=await request.body(),
        )
    except httpx.TimeoutException:
        return JSONResponse(
            status_code=504,
            content={"detail": f"El servicio de {nombre_servicio} no respondió a tiempo"},
        )
    except httpx.RequestError:
        return JSONResponse(
            status_code=503,
            content={"detail": f"El servicio de {nombre_servicio} no está disponible"},
        )

    resultado = Response(content=respuesta.content, status_code=respuesta.status_code)
    cabeceras_respuesta = filtrar_cabeceras(
        respuesta.headers.multi_items(), CABECERAS_EXCLUIDAS_RESPUESTA
    )
    # Usamos append para conservar cabeceras repetidas como set-cookie
    for nombre, valor in cabeceras_respuesta:
        resultado.headers.append(nombre, valor)
    return resultado
