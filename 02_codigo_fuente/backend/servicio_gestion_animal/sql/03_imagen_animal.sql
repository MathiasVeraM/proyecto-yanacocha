-- =============================================================
-- Servicio de Gestión Animal - Fotografía del ejemplar
-- La foto se sube como archivo y se guarda en la base de datos (una por animal),
-- así se respalda junto con el resto de los datos y no depende del disco del servidor.
-- Requiere: 02_taxonomia_y_recintos.sql
-- =============================================================

BEGIN;

CREATE TABLE IF NOT EXISTS gestion_animal.animal_imagen (
    id_animal            INTEGER PRIMARY KEY
        REFERENCES gestion_animal.animal (id_animal) ON DELETE RESTRICT,
    contenido            BYTEA        NOT NULL,
    tipo_mime            VARCHAR(50)  NOT NULL,
    fecha_actualizacion  TIMESTAMP    NOT NULL DEFAULT NOW()
);

COMMIT;
