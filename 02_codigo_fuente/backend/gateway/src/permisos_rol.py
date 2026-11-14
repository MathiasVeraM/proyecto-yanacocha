"""
Qué rol puede hacer cada operación de escritura dentro de un módulo.

El permiso de módulo (tabla rol_permiso, en el token) decide qué módulos ve cada rol en la
barra lateral; estas reglas deciden, dentro del módulo, quién puede crear, editar o eliminar.
Las consultas (GET) no se restringen aquí: el resumen de la ficha también usa diagnósticos y
tratamientos, y todos los roles con el módulo pueden ver la planificación.

Para restringir una ruta nueva basta con agregarla a REGLAS_ESCRITURA. La primera regla que
coincide con la ruta es la que se aplica; las rutas que no coinciden con ninguna no cambian.
"""
import re
from typing import Optional

# Deben coincidir con los id_rol de la tabla rol del servicio de accesos
ID_ROL_ADMIN = 1
ID_ROL_VETERINARIA = 2
ID_ROL_MANEJO_ANIMAL = 3
ID_ROL_VOLUNTARIO = 4

METODOS_LECTURA = {"GET", "HEAD", "OPTIONS"}

# Rol None = cualquier rol con permiso sobre el módulo
_CUALQUIER_ROL = None

# (patrón de la ruta completa, roles que pueden escribir en ella), en orden de prioridad
REGLAS_ESCRITURA: list[tuple[re.Pattern, Optional[frozenset[int]]]] = [
    # ---- Fichas: diagnósticos, tratamientos y sus dosis solo los registra Veterinaria ----
    (
        re.compile(r"^/api/animales/(\d+/)?(diagnosticos|tratamientos)(/.*)?$"),
        frozenset({ID_ROL_VETERINARIA}),
    ),
    # ---- Planificación ----
    # La renovación del horizonte de tomas y dosis se dispara al abrir Planificación
    (
        re.compile(r"^/api/actividades/(tomas|tratamientos)/renovar$"),
        _CUALQUIER_ROL,
    ),
    # Sincroniza las dosis al guardar un tratamiento
    (
        re.compile(r"^/api/actividades/tratamientos/\d+/generar$"),
        frozenset({ID_ROL_VETERINARIA, ID_ROL_MANEJO_ANIMAL}),
    ),
    # Completar una actividad y registrar observaciones
    (
        re.compile(r"^/api/actividades/\d+/(completar|observaciones)$"),
        frozenset({ID_ROL_MANEJO_ANIMAL, ID_ROL_VOLUNTARIO}),
    ),
    # Todo lo demás (crear, editar, eliminar, reabrir, dietas y tomas) es de Manejo de Animales
    (
        re.compile(r"^/api/actividades(/.*)?$"),
        frozenset({ID_ROL_MANEJO_ANIMAL}),
    ),
]


def _normalizar(ruta: str) -> str:
    return ruta.rstrip("/") or "/"


def rol_autorizado(metodo: str, ruta: str, id_rol) -> bool:
    """True si el rol puede hacer esa petición; las lecturas siempre se permiten."""
    if metodo.upper() in METODOS_LECTURA:
        return True
    ruta = _normalizar(ruta)
    for patron, roles in REGLAS_ESCRITURA:
        if patron.match(ruta):
            # isinstance: un id_rol mal formado (ej. una lista) se rechaza en vez de fallar
            return roles is _CUALQUIER_ROL or (isinstance(id_rol, int) and id_rol in roles)
    return True
