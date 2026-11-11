from sqlalchemy import Column, Date, Integer, String, Table, Time

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

if "gestion_animal.diagnostico" not in Base.metadata.tables:
    Table(
        "diagnostico",
        Base.metadata,
        Column("id_diagnostico", Integer, primary_key=True),
        Column("id_animal", Integer, nullable=False),
        schema="gestion_animal",
    )

if "gestion_animal.tratamiento" not in Base.metadata.tables:
    Table(
        "tratamiento",
        Base.metadata,
        Column("id_tratamiento", Integer, primary_key=True),
        Column("id_diagnostico", Integer, nullable=False),
        Column("fecha_inicio", Date, nullable=False),
        Column("fecha_fin", Date),
        Column("frecuencia_valor", Integer),
        Column("frecuencia_unidad", String(10)),
        Column("hora_inicio", Time),
        Column("estado", String(20), nullable=False),
        schema="gestion_animal",
    )
