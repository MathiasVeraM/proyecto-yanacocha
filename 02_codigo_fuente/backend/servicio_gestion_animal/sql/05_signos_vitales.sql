-- =============================================================
-- Servicio de Gestión Animal - Signos vitales veterinarios
-- Crea una relación uno a uno con diagnostico sin alterar esa tabla.
-- =============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS gestion_animal;

CREATE TABLE IF NOT EXISTS gestion_animal.signos_vitales (
    id_signos_vitales            SERIAL PRIMARY KEY,
    id_diagnostico               INTEGER NOT NULL
                                 REFERENCES gestion_animal.diagnostico (id_diagnostico)
                                 ON DELETE RESTRICT,
    peso_kg                      NUMERIC(8, 3),
    temperatura_c                NUMERIC(4, 1),
    frecuencia_cardiaca_lpm      INTEGER,
    frecuencia_respiratoria_rpm  INTEGER,
    tiempo_llenado_capilar_s     NUMERIC(4, 1),
    hidratacion                  VARCHAR(30),
    condicion_corporal           SMALLINT,
    mucosas                      VARCHAR(20),
    actitud                      VARCHAR(20),
    CONSTRAINT ck_signos_vitales_peso_positivo
        CHECK (peso_kg IS NULL OR peso_kg > 0),
    CONSTRAINT ck_signos_vitales_temperatura_rango
        CHECK (temperatura_c IS NULL OR temperatura_c BETWEEN 0 AND 60),
    CONSTRAINT ck_signos_vitales_fc_positiva
        CHECK (frecuencia_cardiaca_lpm IS NULL OR frecuencia_cardiaca_lpm > 0),
    CONSTRAINT ck_signos_vitales_fr_positiva
        CHECK (frecuencia_respiratoria_rpm IS NULL OR frecuencia_respiratoria_rpm > 0),
    CONSTRAINT ck_signos_vitales_tllc_positivo
        CHECK (tiempo_llenado_capilar_s IS NULL OR tiempo_llenado_capilar_s > 0),
    CONSTRAINT ck_signos_vitales_hidratacion
        CHECK (hidratacion IS NULL OR hidratacion IN (
            'normal', 'deshidratacion_leve', 'deshidratacion_moderada', 'deshidratacion_severa'
        )),
    CONSTRAINT ck_signos_vitales_condicion_corporal
        CHECK (condicion_corporal IS NULL OR condicion_corporal BETWEEN 1 AND 5),
    CONSTRAINT ck_signos_vitales_mucosas
        CHECK (mucosas IS NULL OR mucosas IN (
            'rosadas', 'palidas', 'cianoticas', 'ictericas', 'congestionadas'
        )),
    CONSTRAINT ck_signos_vitales_actitud
        CHECK (actitud IS NULL OR actitud IN (
            'alerta', 'deprimido', 'estuporoso', 'agitado'
        )),
    CONSTRAINT ck_signos_vitales_no_vacio
        CHECK (
            peso_kg IS NOT NULL OR temperatura_c IS NOT NULL OR
            frecuencia_cardiaca_lpm IS NOT NULL OR frecuencia_respiratoria_rpm IS NOT NULL OR
            tiempo_llenado_capilar_s IS NOT NULL OR hidratacion IS NOT NULL OR
            condicion_corporal IS NOT NULL OR mucosas IS NOT NULL OR actitud IS NOT NULL
        )
);

-- Índice único: garantiza el uno a uno y acelera las búsquedas por diagnóstico.
CREATE UNIQUE INDEX IF NOT EXISTS ix_signos_vitales_id_diagnostico
    ON gestion_animal.signos_vitales (id_diagnostico);

COMMIT;
