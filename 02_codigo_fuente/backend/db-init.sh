#!/bin/sh
# Crea el esquema de la base de datos ejecutando los scripts SQL de cada servicio EN ORDEN.
# Lo usa el servicio one-shot "db-init" de docker compose (imagen postgres, solo psql).
#
# Orden (por las llaves foráneas entre esquemas):
#   1. accesos/gestion_usuarios.sql      -> tablas rol, modulo, usuario (esquema public)
#   2. gestion_animal/NN_*.sql           -> esquema gestion_animal (01 al 07 hoy)
#   3. actividades/NN_*.sql              -> esquema actividades (01 al 04 hoy)
# Los scripts NN_*.sql nuevos se ejecutan solos, en orden numérico.
#
# Conexión: variables PGHOST, PGUSER, PGPASSWORD y PGDATABASE (las define el compose).
# Los scripts se montan en /sql en solo lectura; no se copian a ninguna imagen.
set -eu

SQL_DIR=/sql

ejecutar() {
    echo "[db-init] $1"
    # Cada script maneja sus propias transacciones (BEGIN/COMMIT), por eso no se usa --single-transaction
    psql -X -q -v ON_ERROR_STOP=1 -f "$1"
}

# Los scripts de usuarios no se pueden repetir; si la base ya tiene las tablas, no se hace nada
# (relevante en desarrollo, donde la base persiste entre ejecuciones).
inicializada=$(psql -X -tA -c "SELECT to_regclass('public.usuario') IS NOT NULL")
if [ "$inicializada" = "t" ]; then
    echo "[db-init] La base de datos ya estaba inicializada; no se ejecutan los scripts."
    exit 0
fi

ejecutar "$SQL_DIR/accesos/gestion_usuarios.sql"

for directorio in gestion_animal actividades; do
    encontrados=0
    for archivo in "$SQL_DIR/$directorio"/[0-9][0-9]_*.sql; do
        [ -f "$archivo" ] || continue
        ejecutar "$archivo"
        encontrados=$((encontrados + 1))
    done
    if [ "$encontrados" -eq 0 ]; then
        echo "[db-init] ERROR: no hay scripts en $SQL_DIR/$directorio" >&2
        exit 1
    fi
done

echo "[db-init] Base de datos inicializada correctamente."
