-- =============================================================
-- Servicio de Actividades - Sincronización offline (HU-09 / HU-10)
-- Agrega un identificador generado en el móvil a cada observación para que
-- reenviarla (reintento de sincronización) nunca la duplique.
-- Requiere 02_observaciones.sql. Se puede ejecutar más de una vez.
-- =============================================================

BEGIN;

ALTER TABLE actividades.observacion_actividad
    ADD COLUMN IF NOT EXISTS id_cliente VARCHAR(64);

-- Único cuando existe; las observaciones creadas desde la web lo dejan en NULL.
CREATE UNIQUE INDEX IF NOT EXISTS ux_observacion_actividad_id_cliente
    ON actividades.observacion_actividad (id_cliente)
    WHERE id_cliente IS NOT NULL;

COMMIT;
