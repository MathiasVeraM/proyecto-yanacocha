-- =============================================================
-- Servicio de Gestión Animal - Taxonomía y recintos (HU-02)
-- - Crea el catálogo de taxonomía (se alimenta con lo que ingresan los usuarios)
-- - Crea los recintos
-- - El animal pasa a referenciar su taxonomía y su recinto (ambos obligatorios);
--   sus columnas taxonómicas se mueven al catálogo
-- Requiere: 01_esquema_gestion_animal.sql
-- =============================================================

BEGIN;

-- Se quitan columnas de animal: solo se permite mientras la tabla esté vacía
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM gestion_animal.animal) THEN
        RAISE EXCEPTION 'gestion_animal.animal tiene datos: este script solo se puede ejecutar con la tabla vacía';
    END IF;
END $$;

-- Catálogo de especies: al escribir el nombre común se autocompletan los demás datos
CREATE TABLE IF NOT EXISTS gestion_animal.taxonomia (
    id_taxonomia  SERIAL PRIMARY KEY,
    nombre_comun  VARCHAR(100) NOT NULL,
    especie       VARCHAR(150) NOT NULL,  -- nombre científico; de aquí salen las iniciales del código
    genero        VARCHAR(100),
    familia       VARCHAR(100),
    -- Si la especie se importó desde iNaturalist, su id allá (evita importarla dos veces)
    id_inaturalist INTEGER UNIQUE
);

-- "Perro" y "perro" son el mismo nombre común
CREATE UNIQUE INDEX IF NOT EXISTS ux_taxonomia_nombre_comun
    ON gestion_animal.taxonomia (LOWER(nombre_comun));

-- Zonas o hábitats donde se ubica cada animal
CREATE TABLE IF NOT EXISTS gestion_animal.recinto (
    id_recinto      SERIAL PRIMARY KEY,
    nombre_recinto  VARCHAR(100) NOT NULL UNIQUE,
    tipo            VARCHAR(50),
    capacidad       INTEGER CHECK (capacidad IS NULL OR capacidad > 0),
    estado          VARCHAR(20) NOT NULL DEFAULT 'disponible'
);

ALTER TABLE gestion_animal.animal
    ADD COLUMN IF NOT EXISTS id_taxonomia INTEGER NOT NULL
        REFERENCES gestion_animal.taxonomia (id_taxonomia) ON DELETE RESTRICT,
    ADD COLUMN IF NOT EXISTS id_recinto INTEGER NOT NULL
        REFERENCES gestion_animal.recinto (id_recinto) ON DELETE RESTRICT,
    DROP COLUMN IF EXISTS nombre_comun,
    DROP COLUMN IF EXISTS especie,
    DROP COLUMN IF EXISTS genero,
    DROP COLUMN IF EXISTS familia;

CREATE INDEX IF NOT EXISTS ix_animal_id_taxonomia ON gestion_animal.animal (id_taxonomia);
CREATE INDEX IF NOT EXISTS ix_animal_id_recinto ON gestion_animal.animal (id_recinto);

COMMIT;
