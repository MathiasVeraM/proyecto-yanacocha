-- =============================================================
-- Servicio de Gestión Animal - Esquema y tablas
-- Tablas: animal, diagnostico, tratamiento (esquema gestion_animal)
-- Se puede ejecutar más de una vez: no borra ni duplica nada.
-- =============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS gestion_animal;

-- Ejemplares del centro de rescate
CREATE TABLE IF NOT EXISTS gestion_animal.animal (
    id_animal              SERIAL PRIMARY KEY,
    codigo_animal          VARCHAR(30)  NOT NULL UNIQUE,
    nombre_comun           VARCHAR(100) NOT NULL,
    especie                VARCHAR(150),
    genero                 VARCHAR(100),  -- género taxonómico, no sexo
    familia                VARCHAR(100),
    edad_aproximada        VARCHAR(50),
    sexo                   VARCHAR(15),
    estado_actual          VARCHAR(30)  NOT NULL DEFAULT 'en_centro',
    fecha_ingreso          DATE         NOT NULL DEFAULT CURRENT_DATE,
    url_imagen             VARCHAR(500)
);

-- Diagnósticos registrados por un usuario (veterinario) sobre un animal
CREATE TABLE IF NOT EXISTS gestion_animal.diagnostico (
    id_diagnostico  SERIAL PRIMARY KEY,
    id_animal       INTEGER   NOT NULL REFERENCES gestion_animal.animal (id_animal) ON DELETE RESTRICT,
    id_usuario      INTEGER   NOT NULL REFERENCES public.usuario (id_usuario) ON DELETE RESTRICT,
    diagnostico     TEXT      NOT NULL,
    observaciones   TEXT,
    es_critico      BOOLEAN   NOT NULL DEFAULT FALSE,
    fecha_registro  TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Tratamientos indicados para un diagnóstico
CREATE TABLE IF NOT EXISTS gestion_animal.tratamiento (
    id_tratamiento         SERIAL PRIMARY KEY,
    id_diagnostico         INTEGER      NOT NULL REFERENCES gestion_animal.diagnostico (id_diagnostico) ON DELETE RESTRICT,
    medicamento_o_proceso  VARCHAR(200) NOT NULL,
    dosis                  VARCHAR(100),
    frecuencia             VARCHAR(100),
    fecha_inicio           DATE         NOT NULL DEFAULT CURRENT_DATE,
    fecha_fin              DATE,
    estado                 VARCHAR(20)  NOT NULL DEFAULT 'en_curso',
    CONSTRAINT ck_tratamiento_fechas CHECK (fecha_fin IS NULL OR fecha_fin >= fecha_inicio)
);

-- Índices para las búsquedas por llave foránea
CREATE INDEX IF NOT EXISTS ix_diagnostico_id_animal ON gestion_animal.diagnostico (id_animal);
CREATE INDEX IF NOT EXISTS ix_diagnostico_id_usuario ON gestion_animal.diagnostico (id_usuario);
CREATE INDEX IF NOT EXISTS ix_tratamiento_id_diagnostico ON gestion_animal.tratamiento (id_diagnostico);

COMMIT;
