from sqlalchemy import Column, Integer, Table

from src.database import Base


def registrar_tabla_referenciada(esquema: str, tabla: str, clave_primaria: str) -> None:
    nombre_completo = f"{esquema}.{tabla}"
    if nombre_completo not in Base.metadata.tables:
        Table(
            tabla,
            Base.metadata,
            Column(clave_primaria, Integer, primary_key=True),
            schema=esquema,
        )


registrar_tabla_referenciada("gestion_animal", "animal", "id_animal")
registrar_tabla_referenciada("gestion_animal", "recinto", "id_recinto")
registrar_tabla_referenciada("public", "usuario", "id_usuario")
