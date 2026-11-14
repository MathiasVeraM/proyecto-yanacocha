from sqlalchemy import Column, Date, Integer, Numeric, String, Table, Text, Time

from src.database import Base

# Estados del animal (gestion_animal.animal.estado_actual) que significan que sigue en el centro
ESTADOS_EN_CENTRO = ("en_centro", "en_tratamiento")


def registrar_tabla_referenciada(esquema: str, tabla: str, clave_primaria: str) -> None:
    nombre_completo = f"{esquema}.{tabla}"
    if nombre_completo not in Base.metadata.tables:
        Table(
            tabla,
            Base.metadata,
            Column(clave_primaria, Integer, primary_key=True),
            schema=esquema,
        )


if "gestion_animal.animal" not in Base.metadata.tables:
    Table(
        "animal",
        Base.metadata,
        Column("id_animal", Integer, primary_key=True),
        # Para no mostrar dosis pendientes de animales que ya salieron del centro
        Column("estado_actual", String(30), nullable=False),
        schema="gestion_animal",
    )
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
        Column("descripcion", Text, nullable=False),
        Column("fecha_inicio", Date, nullable=False),
        Column("fecha_fin", Date),
        Column("frecuencia_valor", Integer),
        Column("frecuencia_unidad", String(10)),
        Column("hora_inicio", Time),
        Column("estado", String(20), nullable=False),
        schema="gestion_animal",
    )

# Medicamentos de cada tratamiento, para mostrarlos con sus dosis en Planificación
if "gestion_animal.tratamiento_medicamento" not in Base.metadata.tables:
    Table(
        "tratamiento_medicamento",
        Base.metadata,
        Column("id_tratamiento_medicamento", Integer, primary_key=True),
        Column("id_tratamiento", Integer, nullable=False),
        Column("nombre_medicamento", String(150), nullable=False),
        Column("dosis_ml", Numeric(8, 2), nullable=False),
        schema="gestion_animal",
    )
