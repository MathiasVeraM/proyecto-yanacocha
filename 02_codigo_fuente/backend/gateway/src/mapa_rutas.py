"""
Relaciona cada ruta del gateway con el servicio (código de la tabla modulo) que debe autorizarla.
Para sumar un servicio nuevo basta con agregar su prefijo a MAPA_MODULOS y, si tiene
rutas que no exigen permiso de módulo, listarlas en RUTAS_PUBLICAS o RUTAS_SOLO_TOKEN.
"""
from dataclasses import dataclass
from typing import Optional

from src.modulos import MODULO_ACCESOS, MODULO_FICHAS_EJEMPLARES

NIVEL_PUBLICA = "publica"  # no exige token
NIVEL_TOKEN = "token"  # exige token válido, sin permiso de módulo
NIVEL_MODULO = "modulo"  # exige token válido y permiso sobre el módulo


@dataclass(frozen=True)
class ReglaAcceso:
    nivel: str
    codigo_servicio: Optional[str] = None


# Coincidencia exacta de (método, ruta)
RUTAS_PUBLICAS = {
    ("POST", "/api/auth/login"),
}

RUTAS_SOLO_TOKEN = {
    # Para mostrar en pantalla, todos los usuarios deben conocer su rol
    ("GET", "/api/auth/roles"),
}

# Prefijo de ruta -> código de servicio
# TODO : agregar los prefijos de los nuevos módulos
MAPA_MODULOS = {
    "/api/auth": MODULO_ACCESOS,
    "/api/animales": MODULO_FICHAS_EJEMPLARES,
}


def _normalizar(ruta: str) -> str:
    return ruta.rstrip("/") or "/"


def resolver_regla(metodo: str, ruta: str) -> Optional[ReglaAcceso]:
    # Devuelve la regla que aplica a la petición, o None si la ruta no está mapeada.
    ruta = _normalizar(ruta)
    clave = (metodo.upper(), ruta)

    if clave in RUTAS_PUBLICAS:
        return ReglaAcceso(NIVEL_PUBLICA)
    if clave in RUTAS_SOLO_TOKEN:
        return ReglaAcceso(NIVEL_TOKEN)

    # El prefijo se compara por segmentos completos: /api/authx no pertenece a /api/auth
    for prefijo, codigo_servicio in MAPA_MODULOS.items():
        if ruta == prefijo or ruta.startswith(f"{prefijo}/"):
            return ReglaAcceso(NIVEL_MODULO, codigo_servicio)
    return None
