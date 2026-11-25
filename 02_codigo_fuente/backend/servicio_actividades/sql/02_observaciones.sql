-- =============================================================
-- Servicio de Actividades - Observaciones de actividades
-- Tablas: observacion_actividad (esquema actividades)
-- Requiere 01_esquema_actividades.sql ejecutado previamente.
-- Se puede ejecutar más de una vez: no borra ni duplica nada.
-- =============================================================

BEGIN;

-- Observaciones registradas sobre una actividad (pendiente o completada).
-- genera_alerta lo calcula el servicio según la HU RF-10:
-- categoria en (comportamiento, estado_fisico) y severidad en (medio, alto).
CREATE TABLE IF NOT EXISTS actividades.observacion_actividad (
    id_observacion  SERIAL PRIMARY KEY,
    id_actividad    INTEGER NOT NULL
                    REFERENCES actividades.actividad (id_actividad) ON DELETE CASCADE,
    categoria       VARCHAR(20) NOT NULL,
    severidad       VARCHAR(10) NOT NULL,
    detalle         TEXT NOT NULL,
    genera_alerta   BOOLEAN NOT NULL DEFAULT FALSE,
    id_usuario      INTEGER NOT NULL,
    fecha_registro  TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_observacion_actividad_categoria
        CHECK (categoria IN ('recinto', 'comportamiento', 'estado_fisico')),
    CONSTRAINT ck_observacion_actividad_severidad
        CHECK (severidad IN ('bajo', 'medio', 'alto'))
);

CREATE INDEX IF NOT EXISTS ix_observacion_actividad_id_actividad
    ON actividades.observacion_actividad (id_actividad);

COMMIT;
