-- =============================================================
-- Servicio de Actividades - Planificación de actividades y dietas
-- Tablas: dieta, dieta_alimento, actividad, actividad_alimentacion,
-- actividad_enriquecimiento, actividad_entrenamiento (esquema actividades)
-- Se puede ejecutar más de una vez: no borra ni duplica nada.
-- =============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS actividades;

-- Planes de alimentación por animal; cada nueva asignación conserva el historial.
CREATE TABLE IF NOT EXISTS actividades.dieta (
    id_dieta             SERIAL PRIMARY KEY,
    id_animal            INTEGER NOT NULL
                         REFERENCES gestion_animal.animal (id_animal) ON DELETE RESTRICT,
    id_usuario_creador   INTEGER NOT NULL
                         REFERENCES public.usuario (id_usuario) ON DELETE RESTRICT,
    fecha_inicio         DATE NOT NULL DEFAULT CURRENT_DATE,
    fecha_fin            DATE,
    frecuencia_valor     INTEGER NOT NULL,
    frecuencia_unidad    VARCHAR(10) NOT NULL,
    vigente              BOOLEAN NOT NULL DEFAULT TRUE,
    observaciones        TEXT,
    fecha_registro       TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_dieta_frecuencia_valor CHECK (frecuencia_valor > 0),
    CONSTRAINT ck_dieta_frecuencia_unidad
        CHECK (frecuencia_unidad IN ('horas', 'dias', 'semanas')),
    CONSTRAINT ck_dieta_fechas
        CHECK (fecha_fin IS NULL OR fecha_fin >= fecha_inicio)
);

-- Alimentos y cantidades que componen una dieta.
CREATE TABLE IF NOT EXISTS actividades.dieta_alimento (
    id_dieta_alimento  SERIAL PRIMARY KEY,
    id_dieta           INTEGER NOT NULL
                       REFERENCES actividades.dieta (id_dieta) ON DELETE RESTRICT,
    nombre_alimento    VARCHAR(150) NOT NULL,
    cantidad_gramos    NUMERIC(8, 2) NOT NULL,
    CONSTRAINT ck_dieta_alimento_cantidad CHECK (cantidad_gramos > 0)
);

-- Actividades programadas, con los datos comunes a todos sus tipos.
CREATE TABLE IF NOT EXISTS actividades.actividad (
    id_actividad          SERIAL PRIMARY KEY,
    tipo_actividad        VARCHAR(20) NOT NULL,
    id_animal             INTEGER
                          REFERENCES gestion_animal.animal (id_animal) ON DELETE RESTRICT,
    id_recinto            INTEGER
                          REFERENCES gestion_animal.recinto (id_recinto) ON DELETE RESTRICT,
    fecha_programada      DATE NOT NULL,
    hora_programada       TIME,
    duracion_horas        SMALLINT NOT NULL DEFAULT 0,
    duracion_minutos      SMALLINT NOT NULL DEFAULT 0,
    id_usuario_programo   INTEGER NOT NULL
                          REFERENCES public.usuario (id_usuario) ON DELETE RESTRICT,
    fecha_registro        TIMESTAMP NOT NULL DEFAULT NOW(),
    completada            BOOLEAN NOT NULL DEFAULT FALSE,
    observaciones         TEXT,
    id_usuario_completo   INTEGER
                          REFERENCES public.usuario (id_usuario) ON DELETE RESTRICT,
    fecha_completada      TIMESTAMP,
    CONSTRAINT ck_actividad_tipo
        CHECK (tipo_actividad IN ('alimentacion', 'enriquecimiento', 'entrenamiento', 'limpieza')),
    CONSTRAINT ck_actividad_duracion_horas CHECK (duracion_horas >= 0),
    CONSTRAINT ck_actividad_duracion_minutos CHECK (duracion_minutos BETWEEN 0 AND 59),
    CONSTRAINT ck_actividad_tipo_destino
        CHECK (
            (
                tipo_actividad = 'limpieza'
                AND id_recinto IS NOT NULL
                AND id_animal IS NULL
                AND (duracion_horas * 60 + duracion_minutos) > 0
            )
            OR
            (
                tipo_actividad IN ('alimentacion', 'enriquecimiento', 'entrenamiento')
                AND id_animal IS NOT NULL
            )
        ),
    CONSTRAINT ck_actividad_entrenamiento_duracion
        CHECK (
            tipo_actividad <> 'entrenamiento'
            OR (duracion_horas * 60 + duracion_minutos) > 0
        ),
    CONSTRAINT ck_actividad_completada
        CHECK (
            NOT completada
            OR (id_usuario_completo IS NOT NULL AND fecha_completada IS NOT NULL)
        )
);

-- Dieta asociada a una actividad de alimentación programada.
CREATE TABLE IF NOT EXISTS actividades.actividad_alimentacion (
    id_actividad  INTEGER PRIMARY KEY
                  REFERENCES actividades.actividad (id_actividad) ON DELETE RESTRICT,
    id_dieta      INTEGER NOT NULL
                  REFERENCES actividades.dieta (id_dieta) ON DELETE RESTRICT
);

-- Estímulo registrado para una actividad de enriquecimiento.
CREATE TABLE IF NOT EXISTS actividades.actividad_enriquecimiento (
    id_actividad           INTEGER PRIMARY KEY
                           REFERENCES actividades.actividad (id_actividad) ON DELETE RESTRICT,
    tipo_enriquecimiento   VARCHAR(20) NOT NULL,
    descripcion_estimulo   TEXT NOT NULL,
    CONSTRAINT ck_actividad_enriquecimiento_tipo
        CHECK (tipo_enriquecimiento IN ('social', 'sensorial', 'alimenticio', 'cognitivo'))
);

-- Objetivos y refuerzo de una actividad de entrenamiento.
CREATE TABLE IF NOT EXISTS actividades.actividad_entrenamiento (
    id_actividad          INTEGER PRIMARY KEY
                          REFERENCES actividades.actividad (id_actividad) ON DELETE RESTRICT,
    objetivo_entrenamiento TEXT NOT NULL,
    tipo_refuerzo         VARCHAR(150) NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_dieta_id_animal_vigente
    ON actividades.dieta (id_animal)
    WHERE vigente;
CREATE INDEX IF NOT EXISTS ix_dieta_id_usuario_creador
    ON actividades.dieta (id_usuario_creador);
CREATE INDEX IF NOT EXISTS ix_dieta_alimento_id_dieta
    ON actividades.dieta_alimento (id_dieta);
CREATE INDEX IF NOT EXISTS ix_actividad_id_animal
    ON actividades.actividad (id_animal);
CREATE INDEX IF NOT EXISTS ix_actividad_id_recinto
    ON actividades.actividad (id_recinto);
CREATE INDEX IF NOT EXISTS ix_actividad_fecha_programada
    ON actividades.actividad (fecha_programada);
CREATE INDEX IF NOT EXISTS ix_actividad_id_usuario_programo
    ON actividades.actividad (id_usuario_programo);
CREATE INDEX IF NOT EXISTS ix_actividad_id_usuario_completo
    ON actividades.actividad (id_usuario_completo);
CREATE INDEX IF NOT EXISTS ix_actividad_alimentacion_id_actividad
    ON actividades.actividad_alimentacion (id_actividad);
CREATE INDEX IF NOT EXISTS ix_actividad_alimentacion_id_dieta
    ON actividades.actividad_alimentacion (id_dieta);
CREATE INDEX IF NOT EXISTS ix_actividad_enriquecimiento_id_actividad
    ON actividades.actividad_enriquecimiento (id_actividad);
CREATE INDEX IF NOT EXISTS ix_actividad_entrenamiento_id_actividad
    ON actividades.actividad_entrenamiento (id_actividad);

COMMIT;
