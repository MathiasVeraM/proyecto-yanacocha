from sqlalchemy import func
from sqlalchemy.orm import Session
from src.modelos.animal_model import TaxonomiaModel

class TaxonomiaRepository:
    @staticmethod
    def buscar(db: Session, texto: str | None = None, limite: int | None = None):
        # Busca por nombre común o científico, sin distinguir mayúsculas
        consulta = db.query(TaxonomiaModel)
        if texto:
            patron = f"%{texto}%"
            consulta = consulta.filter(
                TaxonomiaModel.nombre_comun.ilike(patron) | TaxonomiaModel.especie.ilike(patron)
            )
        consulta = consulta.order_by(TaxonomiaModel.nombre_comun)
        if limite:
            consulta = consulta.limit(limite)
        return consulta.all()

    @staticmethod
    def obtener_por_id(db: Session, id_taxonomia: int):
        return db.query(TaxonomiaModel).filter(TaxonomiaModel.id_taxonomia == id_taxonomia).first()

    @staticmethod
    def obtener_por_nombre_comun(db: Session, nombre_comun: str):
        return (
            db.query(TaxonomiaModel)
            .filter(func.lower(TaxonomiaModel.nombre_comun) == nombre_comun.lower())
            .first()
        )

    @staticmethod
    def obtener_por_id_inaturalist(db: Session, id_inaturalist: int):
        return db.query(TaxonomiaModel).filter(TaxonomiaModel.id_inaturalist == id_inaturalist).first()

    @staticmethod
    def obtener_ids_inaturalist(db: Session, ids: list[int]) -> set[int]:
        if not ids:
            return set()
        filas = db.query(TaxonomiaModel.id_inaturalist).filter(TaxonomiaModel.id_inaturalist.in_(ids)).all()
        return {fila.id_inaturalist for fila in filas}

    @staticmethod
    def crear_taxonomia(db: Session, taxonomia_data: dict):
        taxonomia = TaxonomiaModel(**taxonomia_data)
        db.add(taxonomia)
        db.commit()
        db.refresh(taxonomia)
        return taxonomia

    @staticmethod
    def actualizar_taxonomia(db: Session, taxonomia: TaxonomiaModel, datos: dict):
        for campo, valor in datos.items():
            setattr(taxonomia, campo, valor)
        db.commit()
        db.refresh(taxonomia)
        return taxonomia
