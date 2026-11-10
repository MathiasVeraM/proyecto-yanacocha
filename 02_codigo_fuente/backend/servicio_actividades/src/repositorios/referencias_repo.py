from sqlalchemy import Column, Integer, MetaData, Table, select
from sqlalchemy.orm import Session


_METADATA = MetaData()
_TABLAS_REFERENCIA = {
    ("gestion_animal", "animal"): Table(
        "animal",
        _METADATA,
        Column("id_animal", Integer, primary_key=True),
        schema="gestion_animal",
    ),
    ("gestion_animal", "recinto"): Table(
        "recinto",
        _METADATA,
        Column("id_recinto", Integer, primary_key=True),
        schema="gestion_animal",
    ),
}


class ReferenciasRepository:
    @staticmethod
    def existe(db: Session, esquema: str, tabla: str, columna: str, valor: int) -> bool:
        referencia = _TABLAS_REFERENCIA[(esquema, tabla)]
        return db.execute(
            select(referencia.c[columna]).where(referencia.c[columna] == valor)
        ).scalar_one_or_none() is not None

    @staticmethod
    def existe_animal(db: Session, id_animal: int) -> bool:
        return ReferenciasRepository.existe(
            db, "gestion_animal", "animal", "id_animal", id_animal
        )

    @staticmethod
    def existe_recinto(db: Session, id_recinto: int) -> bool:
        return ReferenciasRepository.existe(
            db, "gestion_animal", "recinto", "id_recinto", id_recinto
        )
