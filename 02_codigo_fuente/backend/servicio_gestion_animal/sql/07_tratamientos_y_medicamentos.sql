-- =============================================================
-- Servicio de Gestión Animal - Tratamientos y medicamentos
-- Tablas: tratamiento, tratamiento_medicamento (esquema gestion_animal)
-- Se puede ejecutar más de una vez: no borra ni duplica nada.
-- =============================================================

BEGIN;

ALTER TABLE gestion_animal.tratamiento
    ADD COLUMN IF NOT EXISTS descripcion TEXT,
    ADD COLUMN IF NOT EXISTS frecuencia_valor INTEGER,
    ADD COLUMN IF NOT EXISTS frecuencia_unidad VARCHAR(10),
    ADD COLUMN IF NOT EXISTS hora_inicio TIME;

-- Conserva el texto existente como descripción, sin interpretar dosis o frecuencias antiguas.
UPDATE gestion_animal.tratamiento
SET descripcion = COALESCE(
    NULLIF(BTRIM(descripcion), ''),
    NULLIF(BTRIM(medicamento_o_proceso), ''),
    'Tratamiento registrado antes de la actualización'
)
WHERE descripcion IS NULL OR LENGTH(BTRIM(descripcion)) = 0;

ALTER TABLE gestion_animal.tratamiento
    ALTER COLUMN descripcion SET NOT NULL;

-- Se conservan las columnas antiguas y sus datos, pero dejan de ser obligatorias para nuevos registros.
ALTER TABLE gestion_animal.tratamiento
    ALTER COLUMN medicamento_o_proceso DROP NOT NULL;

DO $$
DECLARE
    tabla_tratamiento CONSTANT regclass := 'gestion_animal.tratamiento'::regclass;
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_tratamiento_fechas'
          AND conrelid = tabla_tratamiento
    ) THEN
        ALTER TABLE gestion_animal.tratamiento
            ADD CONSTRAINT ck_tratamiento_fechas
            CHECK (fecha_fin IS NULL OR fecha_fin >= fecha_inicio);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_tratamiento_frecuencia_valor'
          AND conrelid = tabla_tratamiento
    ) THEN
        ALTER TABLE gestion_animal.tratamiento
            ADD CONSTRAINT ck_tratamiento_frecuencia_valor
            CHECK (frecuencia_valor IS NULL OR frecuencia_valor > 0);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_tratamiento_frecuencia_unidad'
          AND conrelid = tabla_tratamiento
    ) THEN
        ALTER TABLE gestion_animal.tratamiento
            ADD CONSTRAINT ck_tratamiento_frecuencia_unidad
            CHECK (frecuencia_unidad IS NULL OR frecuencia_unidad IN ('horas', 'dias'));
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_tratamiento_frecuencia_completa'
          AND conrelid = tabla_tratamiento
    ) THEN
        ALTER TABLE gestion_animal.tratamiento
            ADD CONSTRAINT ck_tratamiento_frecuencia_completa
            CHECK ((frecuencia_valor IS NULL) = (frecuencia_unidad IS NULL));
    END IF;
END
$$;

-- Medicamentos opcionales del tratamiento; las frecuencias antiguas quedan sin conversión implícita.
CREATE TABLE IF NOT EXISTS gestion_animal.tratamiento_medicamento (
    id_tratamiento_medicamento SERIAL PRIMARY KEY,
    id_tratamiento             INTEGER NOT NULL
                               REFERENCES gestion_animal.tratamiento (id_tratamiento) ON DELETE RESTRICT,
    nombre_medicamento         VARCHAR(150) NOT NULL,
    dosis_ml                   NUMERIC(8, 2) NOT NULL,
    CONSTRAINT ck_tratamiento_medicamento_dosis CHECK (dosis_ml > 0)
);

CREATE INDEX IF NOT EXISTS ix_tratamiento_medicamento_id_tratamiento
    ON gestion_animal.tratamiento_medicamento (id_tratamiento);

COMMIT;
