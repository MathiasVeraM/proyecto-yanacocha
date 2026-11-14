-- =============================================================
-- Servicio de Actividades - Validaciones de actividades
-- Respaldo en la base del "duplicado exacto" (validación 25): no puede haber dos actividades
-- programadas a mano del mismo tipo, para el mismo ejemplar o recinto, el mismo día y a la misma
-- hora. El servicio responde 409 antes de llegar aquí; el índice frena el caso de dos personas
-- guardando la misma actividad al mismo tiempo.
-- Las tomas de alimentación y las dosis de tratamiento las genera el sistema y tienen su propio
-- control, por eso quedan fuera del índice.
-- Requiere: 01_esquema_actividades.sql
-- Se puede ejecutar más de una vez.
-- =============================================================

BEGIN;

CREATE UNIQUE INDEX IF NOT EXISTS ux_actividad_manual_unica
    ON actividades.actividad (
        tipo_actividad,
        COALESCE(id_animal, 0),
        COALESCE(id_recinto, 0),
        fecha_programada,
        hora_programada
    )
    WHERE tipo_actividad IN ('enriquecimiento', 'entrenamiento', 'limpieza');

COMMIT;
