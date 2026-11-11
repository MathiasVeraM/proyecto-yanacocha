BEGIN;

ALTER TABLE gestion_animal.animal
    ADD COLUMN IF NOT EXISTS edad_anios SMALLINT,
    ADD COLUMN IF NOT EXISTS edad_meses SMALLINT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_animal_edad_anios'
          AND conrelid = 'gestion_animal.animal'::regclass
    ) THEN
        ALTER TABLE gestion_animal.animal
            ADD CONSTRAINT ck_animal_edad_anios
            CHECK (edad_anios IS NULL OR edad_anios >= 0);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_animal_edad_meses'
          AND conrelid = 'gestion_animal.animal'::regclass
    ) THEN
        ALTER TABLE gestion_animal.animal
            ADD CONSTRAINT ck_animal_edad_meses
            CHECK (edad_meses IS NULL OR edad_meses BETWEEN 0 AND 11);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_animal_edad_completa'
          AND conrelid = 'gestion_animal.animal'::regclass
    ) THEN
        ALTER TABLE gestion_animal.animal
            ADD CONSTRAINT ck_animal_edad_completa
            CHECK (
                (edad_anios IS NULL AND edad_meses IS NULL)
                OR (edad_anios IS NOT NULL AND edad_meses IS NOT NULL)
            );
    END IF;
END
$$;

COMMIT;