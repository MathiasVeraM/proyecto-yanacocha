from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.logica_negocio import inaturalist
from src.logica_negocio.codigo_animal import iniciales
from src.logica_negocio.utilidades import datos_a_actualizar
from src.repositorios.taxonomia_repo import TaxonomiaRepository

CAMPOS_OBLIGATORIOS = {"nombre_comun", "especie"}
LIMITE_SUGERENCIAS = 10

def _validar_especie(especie: str):
    if not iniciales(especie):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre científico debe contener letras"
        )

def _nombre_comun_repetido():
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Ya existe una especie con ese nombre común en el catálogo"
    )

class TaxonomiaService:
    @staticmethod
    def taxonomia_o_404(db: Session, id_taxonomia: int):
        taxonomia = TaxonomiaRepository.obtener_por_id(db, id_taxonomia)
        if not taxonomia:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Especie no encontrada")
        return taxonomia

    @staticmethod
    def buscar(db: Session, texto: str | None):
        return TaxonomiaRepository.buscar(db, texto)

    @staticmethod
    def crear_taxonomia(db: Session, taxonomia_in):
        _validar_especie(taxonomia_in.especie)
        if TaxonomiaRepository.obtener_por_nombre_comun(db, taxonomia_in.nombre_comun):
            raise _nombre_comun_repetido()
        return TaxonomiaRepository.crear_taxonomia(db, taxonomia_in.model_dump())

    @staticmethod
    def actualizar_taxonomia(db: Session, id_taxonomia: int, taxonomia_in):
        taxonomia = TaxonomiaService.taxonomia_o_404(db, id_taxonomia)
        datos = datos_a_actualizar(taxonomia_in, CAMPOS_OBLIGATORIOS)
        if "especie" in datos:
            _validar_especie(datos["especie"])
        nombre = datos.get("nombre_comun")
        if nombre and nombre.lower() != taxonomia.nombre_comun.lower():
            if TaxonomiaRepository.obtener_por_nombre_comun(db, nombre):
                raise _nombre_comun_repetido()
        return TaxonomiaRepository.actualizar_taxonomia(db, taxonomia, datos)

    @staticmethod
    def sugerencias(db: Session, texto: str):
        # Primero lo que ya está en el catálogo; luego lo que sugiere iNaturalist y todavía no se importó
        locales = TaxonomiaRepository.buscar(db, texto, limite=LIMITE_SUGERENCIAS)
        resultado = [
            {
                "origen": "catalogo",
                "id_taxonomia": t.id_taxonomia,
                "id_inaturalist": t.id_inaturalist,
                "nombre_comun": t.nombre_comun,
                "especie": t.especie,
            }
            for t in locales
        ]
        externas = inaturalist.buscar_especies(texto)
        ya_importadas = TaxonomiaRepository.obtener_ids_inaturalist(db, [e["id_inaturalist"] for e in externas])
        resultado += [
            {"origen": "inaturalist", **e}
            for e in externas
            if e["id_inaturalist"] not in ya_importadas
        ]
        return resultado

    @staticmethod
    def importar_de_inaturalist(db: Session, id_inaturalist: int):
        existente = TaxonomiaRepository.obtener_por_id_inaturalist(db, id_inaturalist)
        if existente:
            return existente

        try:
            datos = inaturalist.obtener_especie(id_inaturalist)
        except inaturalist.INaturalistNoDisponible:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="iNaturalist no está disponible; intenta más tarde o registra la especie manualmente"
            )
        if datos is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La especie no existe en iNaturalist o no es una especie animal"
            )

        # Algunas especies no tienen nombre común en español; se usa el científico
        datos["nombre_comun"] = datos["nombre_comun"] or datos["especie"]
        if TaxonomiaRepository.obtener_por_nombre_comun(db, datos["nombre_comun"]):
            raise _nombre_comun_repetido()
        return TaxonomiaRepository.crear_taxonomia(db, datos)
