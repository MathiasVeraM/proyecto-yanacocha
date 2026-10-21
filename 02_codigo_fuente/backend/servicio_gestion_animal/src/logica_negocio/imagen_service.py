from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.logica_negocio.animal_service import AnimalService
from src.modelos.animal_model import ahora_local
from src.repositorios.animal_repo import AnimalRepository
from src.repositorios.imagen_repo import ImagenRepository

TAMANO_MAXIMO = 5 * 1024 * 1024  # 5 MB

# El tipo se decide por los primeros bytes del archivo, no por la extensión ni por lo que diga el navegador
FIRMAS = [
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
]

def detectar_tipo(contenido: bytes) -> str | None:
    for firma, tipo in FIRMAS:
        if contenido.startswith(firma):
            return tipo
    if contenido[:4] == b"RIFF" and contenido[8:12] == b"WEBP":
        return "image/webp"
    return None

class ImagenService:
    @staticmethod
    def guardar_imagen(db: Session, id_animal: int, archivo):
        animal = AnimalService.animal_o_404(db, id_animal)
        # Se lee un byte de más para saber si el archivo supera el límite sin cargarlo entero
        contenido = archivo.read(TAMANO_MAXIMO + 1)
        if len(contenido) > TAMANO_MAXIMO:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail="La fotografía no puede superar los 5 MB"
            )
        tipo = detectar_tipo(contenido)
        if tipo is None:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="La fotografía debe ser una imagen JPG, PNG o WEBP"
            )
        ImagenRepository.guardar(db, id_animal, contenido, tipo)
        # El parámetro v cambia en cada subida para que el navegador no muestre la foto anterior guardada en caché
        url = f"/api/animales/{id_animal}/imagen?v={int(ahora_local().timestamp())}"
        return AnimalRepository.actualizar_animal(db, animal, {"url_imagen": url})

    @staticmethod
    def obtener_imagen(db: Session, id_animal: int):
        AnimalService.animal_o_404(db, id_animal)
        imagen = ImagenRepository.obtener(db, id_animal)
        if not imagen:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El animal no tiene fotografía")
        return imagen
