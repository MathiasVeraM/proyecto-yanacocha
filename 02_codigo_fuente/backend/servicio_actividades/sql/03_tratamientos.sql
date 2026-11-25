-- =============================================================
-- Servicio de Actividades - Actividades programadas de tratamiento
-- Tablas: actividad, actividad_tratamiento (esquema actividades)
-- Se puede ejecutar más de una vez: no borra ni duplica nada.
-- =============================================================

BEGIN;

ALTER TABLE actividades.actividad
    DROP CONSTRAINT IF EXISTS ck_actividad_tipo;

ALTER TABLE actividades.actividad
    ADD CONSTRAINT ck_actividad_tipo
    CHECK (
        tipo_actividad IN (
            'alimentacion',
            'enriquecimiento',
            'entrenamiento',
            'limpieza',
            'tratamiento'
        )
    );

ALTER TABLE actividades.actividad
    DROP CONSTRAINT IF EXISTS ck_actividad_tipo_destino;

ALTER TABLE actividades.actividad
    ADD CONSTRAINT ck_actividad_tipo_destino
    CHECK (
        (
            tipo_actividad = 'limpieza'
            AND id_recinto IS NOT NULL
            AND id_animal IS NULL
            AND (duracion_horas * 60 + duracion_minutos) > 0
        )
        OR
        (
            tipo_actividad IN (
                'alimentacion',
                'enriquecimiento',
                'entrenamiento',
                'tratamiento'
            )
            AND id_animal IS NOT NULL
        )
    );

-- Asociación y clave de idempotencia para las dosis programadas.
CREATE TABLE IF NOT EXISTS actividades.actividad_tratamiento (
    id_actividad       INTEGER PRIMARY KEY
                       REFERENCES actividades.actividad (id_actividad) ON DELETE RESTRICT,
    id_tratamiento    INTEGER NOT NULL
                       REFERENCES gestion_animal.tratamiento (id_tratamiento) ON DELETE RESTRICT,
    fecha_programada  DATE NOT NULL,
    hora_programada   TIME NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_actividad_tratamiento_programacion
    ON actividades.actividad_tratamiento (id_tratamiento, fecha_programada, hora_programada);

COMMIT;
