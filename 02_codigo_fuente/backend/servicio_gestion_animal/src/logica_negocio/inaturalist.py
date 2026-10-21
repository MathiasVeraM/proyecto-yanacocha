"""Consulta a la API pública de iNaturalist para sugerir e importar especies."""
import httpx2
from src.config import INATURALIST_TIMEOUT_SECONDS, INATURALIST_URL

ID_TAXON_ANIMALIA = 1  # filtra plantas, hongos y demás reinos
RANGOS_VALIDOS = {"species", "subspecies"}  # el código necesita el nombre científico completo

class INaturalistNoDisponible(Exception):
    """iNaturalist no respondió o respondió con error."""

def crear_cliente() -> httpx2.Client:
    return httpx2.Client(
        base_url=INATURALIST_URL,
        timeout=INATURALIST_TIMEOUT_SECONDS,
        headers={"User-Agent": "Yanacocha-GestionAnimal/1.0"},
    )

def _es_animal_valido(taxon: dict) -> bool:
    return taxon.get("rank") in RANGOS_VALIDOS and ID_TAXON_ANIMALIA in taxon.get("ancestor_ids", [])

def buscar_especies(texto: str, limite: int = 5) -> list[dict]:
    """Sugerencias por nombre común o científico. Si iNaturalist falla devuelve [] para no bloquear al usuario."""
    try:
        with crear_cliente() as cliente:
            respuesta = cliente.get(
                "/taxa/autocomplete",
                params={"q": texto, "locale": "es", "taxon_id": ID_TAXON_ANIMALIA, "per_page": 20},
            )
            respuesta.raise_for_status()
            resultados = respuesta.json().get("results", [])
    except (httpx2.HTTPError, ValueError):
        return []

    especies = [
        {
            "id_inaturalist": taxon["id"],
            "nombre_comun": taxon.get("preferred_common_name"),
            "especie": taxon["name"],
        }
        for taxon in resultados
        if _es_animal_valido(taxon)
    ]
    return especies[:limite]

def obtener_especie(id_inaturalist: int) -> dict | None:
    """Datos completos de una especie, o None si no existe o no es una especie animal."""
    try:
        with crear_cliente() as cliente:
            respuesta = cliente.get(f"/taxa/{id_inaturalist}", params={"locale": "es"})
            respuesta.raise_for_status()
            resultados = respuesta.json().get("results", [])
    except (httpx2.HTTPError, ValueError) as error:
        raise INaturalistNoDisponible() from error

    if not resultados or not _es_animal_valido(resultados[0]):
        return None
    taxon = resultados[0]
    ancestros = {a.get("rank"): a.get("name") for a in taxon.get("ancestors", [])}
    return {
        "id_inaturalist": taxon["id"],
        "nombre_comun": taxon.get("preferred_common_name"),
        "especie": taxon["name"],
        "genero": ancestros.get("genus"),
        "familia": ancestros.get("family"),
    }
