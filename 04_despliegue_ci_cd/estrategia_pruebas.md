# ESTRATEGIA DE PRUEBAS

## Niveles de prueba

| Nivel | Qué verifica | Herramienta | Dónde corre |
|---|---|---|---|
| Unitarias | Lógica de cada servicio, con dependencias externas simuladas (mocks) | pytest, pytest-cov | Runner de GitHub, sin Docker |
| Integración | Que los servicios, la base de datos y la imagen Docker funcionen juntos | pytest + httpx + Docker Compose | Runner de GitHub, contenedores efímeros |

## Estructura de carpetas

```
02_codigo_fuente/
├── backend/
│   └── <servicio>/
│       ├── app/
│       ├── tests/            # pruebas unitarias del servicio
│       ├── pytest.ini
│       ├── requirements.txt
│       └── Dockerfile        # multi-stage
├── tests_integracion/        # pruebas de integración (todo el sistema)
└── docker-compose.test.yml   # entorno efímero para integración
```

## Pruebas unitarias

- Cada servicio tiene su propia carpeta `tests/` y su `pytest.ini` (con `pythonpath = .`).
- Archivos `test_*.py`, funciones `test_<comportamiento>()`.
- Base de datos y servicios externos se reemplazan con mocks o fixtures.
- Se ejecutan por servicio con una matriz de GitHub Actions.
- Cada ejecución genera un reporte de cobertura `coverage-<servicio>.xml`,
  que SonarQube consume.

Comando local:

    pytest 02_codigo_fuente/backend/<servicio> \
      --cov=02_codigo_fuente/backend/<servicio> \
      --cov-report=xml:coverage-<servicio>.xml

## Pruebas de integración

- Viven en `02_codigo_fuente/tests_integracion/`.
- Usan peticiones HTTP reales (httpx) contra los contenedores levantados.
- El entorno se define en `docker-compose.test.yml`:
  - Un contenedor por servicio, construido con la etapa `runtime` del Dockerfile
    (la misma imagen que se desplegará).
  - Base de datos de prueba como contenedor efímero.
  - `healthcheck` en cada servicio, para esperar con `up --wait`.
- Casos mínimos por servicio:
  1. `/health` responde 200.
  2. Un flujo de escritura y lectura real (crear y consultar un recurso).
  3. Comunicación entre servicios, cuando aplique.
- Al terminar, el entorno se destruye (`down -v`). Si falla, se imprimen los logs.

Comando local:

    docker compose -f 02_codigo_fuente/docker-compose.test.yml up -d --build --wait
    pytest 02_codigo_fuente/tests_integracion
    docker compose -f 02_codigo_fuente/docker-compose.test.yml down -v

## Criterios de aceptación

- Todas las pruebas que se definan, unitarias y de integración, deben pasar.
- Cobertura mínima en código nuevo: **80 %** (se valida en SonarQube, ver `quality_gates.md`).
- Todo servicio nuevo debe incluir al menos pruebas unitarias y su caso `/health`
  en integración.

## Frontend (TypeScript)

(Por definir: framework de pruebas, por ejemplo Vitest o Jest, y su reporte `lcov`
para SonarQube.)

## Datos de prueba

- No se usan datos reales ni secretos en las pruebas.
- Las credenciales del entorno de integración son valores de prueba definidos
  en `docker-compose.test.yml`.