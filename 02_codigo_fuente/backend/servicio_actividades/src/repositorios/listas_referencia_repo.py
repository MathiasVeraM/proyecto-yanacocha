from sqlalchemy import Boolean, Column, Integer, MetaData, String, Table, Text, cast, literal_column, null, select, union_all
from sqlalchemy.orm import Session

# Tablas de otros servicios (misma base de datos), solo las columnas que se leen. Metadata propia
# para no mezclarlas con los modelos de este servicio.
_METADATA = MetaData()
_ANIMAL = Table(
    "animal",
    _METADATA,
    Column("id_animal", Integer, primary_key=True),
    Column("codigo_animal", String),
    Column("nombre", String),
    Column("id_taxonomia", Integer),
    Column("id_recinto", Integer),
    Column("estado_actual", String),
    schema="gestion_animal",
)
_TAXONOMIA = Table(
    "taxonomia",
    _METADATA,
    Column("id_taxonomia", Integer, primary_key=True),
    Column("nombre_comun", String),
    Column("especie", String),
    Column("clase", String),
    schema="gestion_animal",
)
_RECINTO = Table(
    "recinto",
    _METADATA,
    Column("id_recinto", Integer, primary_key=True),
    Column("nombre_recinto", String),
    Column("tipo", String),
    Column("capacidad", Integer),
    Column("estado", String),
    schema="gestion_animal",
)
_USUARIO = Table(
    "usuario",
    _METADATA,
    Column("id_usuario", Integer, primary_key=True),
    Column("nombre", String),
    Column("apellido", String),
    Column("activo", Boolean),
    schema="public",
)


def _texto_nulo():
    return cast(null(), Text)


def _entero_nulo():
    return cast(null(), Integer)


class ListasReferenciaRepository:
    @staticmethod
    def obtener_todas(db: Session):
        """Ejemplares, recintos y usuarios en UNA sola consulta (un solo viaje a la base).

        Con la base remota cada ida y vuelta cuesta ~200 ms; tres consultas por separado serían
        ~600 ms. Las filas comparten forma: tipo, id, t1..t6 (texto) y n1, n2 (número); cada
        tipo usa las columnas que necesita. Devuelve filas con esa forma (ver el servicio).
        """
        animales = (
            select(
                literal_column("'animal'").label("tipo"),
                _ANIMAL.c.id_animal.label("id"),
                _ANIMAL.c.codigo_animal.label("t1"),
                _ANIMAL.c.nombre.label("t2"),
                _ANIMAL.c.estado_actual.label("t3"),
                _TAXONOMIA.c.nombre_comun.label("t4"),
                _TAXONOMIA.c.especie.label("t5"),
                _TAXONOMIA.c.clase.label("t6"),
                _ANIMAL.c.id_taxonomia.label("n1"),
                _ANIMAL.c.id_recinto.label("n2"),
            ).select_from(_ANIMAL.join(_TAXONOMIA, _TAXONOMIA.c.id_taxonomia == _ANIMAL.c.id_taxonomia))
        )
        recintos = select(
            literal_column("'recinto'"),
            _RECINTO.c.id_recinto,
            _RECINTO.c.nombre_recinto,
            _RECINTO.c.tipo,
            _RECINTO.c.estado,
            _texto_nulo(),
            _texto_nulo(),
            _texto_nulo(),
            _RECINTO.c.capacidad,
            _entero_nulo(),
        )
        usuarios = select(
            literal_column("'usuario'"),
            _USUARIO.c.id_usuario,
            _USUARIO.c.nombre,
            _USUARIO.c.apellido,
            _texto_nulo(),
            _texto_nulo(),
            _texto_nulo(),
            _texto_nulo(),
            cast(_USUARIO.c.activo, Integer),
            _entero_nulo(),
        )
        return db.execute(union_all(animales, recintos, usuarios)).all()
