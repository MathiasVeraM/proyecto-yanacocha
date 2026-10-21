from sqlalchemy.orm import Session
from src.modelos.animal_model import AnimalImagenModel

class ImagenRepository:
    @staticmethod
    def obtener(db: Session, id_animal: int):
        return db.query(AnimalImagenModel).filter(AnimalImagenModel.id_animal == id_animal).first()

    @staticmethod
    def guardar(db: Session, id_animal: int, contenido: bytes, tipo_mime: str):
        # Cada animal tiene una sola foto: si ya había una, se reemplaza
        imagen = ImagenRepository.obtener(db, id_animal)
        if imagen:
            imagen.contenido = contenido
            imagen.tipo_mime = tipo_mime
        else:
            imagen = AnimalImagenModel(id_animal=id_animal, contenido=contenido, tipo_mime=tipo_mime)
            db.add(imagen)
        db.commit()
        db.refresh(imagen)
        return imagen
