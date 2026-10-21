-- =============================================================
-- Servicio de Gestión Animal - Clase y orden taxonómicos, y nombre del ejemplar
-- - taxonomia.clase y taxonomia.orden (ej. Mammalia / Carnivora); se llenan solos al importar de iNaturalist
-- - animal.nombre: nombre propio del ejemplar (ej. "Yaku"), distinto del nombre común de la especie
-- Columnas opcionales: no afectan a los registros que ya existen.
-- Requiere: 03_imagen_animal.sql
-- =============================================================

BEGIN;

ALTER TABLE gestion_animal.taxonomia
    ADD COLUMN IF NOT EXISTS clase VARCHAR(100),
    ADD COLUMN IF NOT EXISTS orden VARCHAR(100);

ALTER TABLE gestion_animal.animal
    ADD COLUMN IF NOT EXISTS nombre VARCHAR(100);

-- Los filtros del catálogo de animales agrupan por clase (Mamíferos, Aves, Reptiles…)
CREATE INDEX IF NOT EXISTS ix_taxonomia_clase ON gestion_animal.taxonomia (clase);

COMMIT;
