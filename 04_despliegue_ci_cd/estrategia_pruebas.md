# ESTRATEGIA DE PRUEBAS

## Niveles de prueba

| Nivel | Qué verifica | Herramienta | Dónde corre |
|---|---|---|---|
| Unitarias | Lógica de cada servicio, con dependencias externas simuladas (mocks, SQLite en memoria) | pytest, pytest-cov | Runner de GitHub, sin Docker |
| Integración | Que gateway, servicios y base de datos funcionen juntos, por HTTP real y sin mocks | pytest + httpx + Docker Compose | Runner de GitHub, contenedores efímeros |

## Estructura de carpetas

```
02_codigo_fuente/
└── backend/
    ├── <servicio>/
    │   ├── src/
    │   ├── tests/                  # pruebas unitarias del servicio
    │   ├── pytest.ini
    │   ├── requirements.txt        # solo ejecución (lo que entra en la imagen)
    │   ├── requirements-dev.txt    # -r requirements.txt + pytest, pytest-cov, cliente de TestClient
    │   ├── Dockerfile              # multi-stage: builder, test y runtime
    │   └── .dockerignore
    ├── docker-compose.yml          # desarrollo y servidor (sin base de datos propia)
    ├── docker-compose.local-db.yml # complemento opcional: PostgreSQL local y limpia
    ├── docker-compose.test.yml     # entorno efímero de las pruebas de integración
    └── db-init.sh                  # ejecuta los scripts SQL en orden (db-init del compose)
03_pruebas/
└── integracion/                    # pruebas de integración (todo el sistema)
```

Las pruebas de integración están **fuera de `backend/`** a propósito: `_backend-tests.yml` crea un job por cada
carpeta de `backend/` y las correría como si fueran unitarias. Por la misma razón no se crean carpetas nuevas
dentro de `backend/` que no sean servicios.

## Pruebas unitarias

- Cada servicio tiene su propia carpeta `tests/` y su `pytest.ini` (con `pythonpath = .`).
- Archivos `test_*.py`, funciones `test_<comportamiento>()`.
- Base de datos y servicios externos se reemplazan con mocks o fixtures.
- Se ejecutan por servicio con una matriz de GitHub Actions, instalando `requirements-dev.txt`.
- Cada ejecución genera un reporte de cobertura `coverage-<servicio>.xml`, que SonarQube consume.
- Cada servicio y el gateway tienen `tests/test_health.py` (liveness, readiness y que no se filtren datos). En el
  gateway se prueba además que `/health` no entra en `mapa_rutas.py` y que las rutas desconocidas siguen rechazadas.

Comando local:

    cd 02_codigo_fuente/backend/<servicio>
    pip install -r requirements-dev.txt
    pytest

## Pruebas de integración

- Viven en `03_pruebas/integracion/`, con su propio `conftest.py`, `pytest.ini` y `requirements-dev.txt`.
- Hacen peticiones HTTP reales (httpx) **solo al gateway**, contra los contenedores de `docker-compose.test.yml`.
- `docker-compose.test.yml` es **independiente** (no un override del de desarrollo), para que no pueda heredar
  volúmenes, puertos ni credenciales de otro entorno:
  - Gateway y tres servicios, construidos con la etapa `runtime` de cada Dockerfile (la misma imagen que se despliega).
  - Base PostgreSQL 17 **efímera**: vive en memoria (`tmpfs`), sin volumen, con nombre y usuario propios.
  - Servicios `db-init` (scripts SQL en orden, montados en solo lectura) y `admin-init` (primer administrador con
    `crear_admin.py`). Los servicios arrancan solo si ambos terminaron bien.
  - Solo el gateway publica puerto, y solo en `127.0.0.1`. Las redes de datos y servicios son internas.
  - `no-new-privileges`, `cap_drop: ALL` y sistema de archivos de solo lectura en la aplicación.
  - `healthcheck` en cada servicio (`GET /health`), para esperar con `up --wait`.
- Un archivo por área: salud, autenticación y módulos, permisos por rol, gestión animal, actividades, dietas y
  tomas, e integración entre servicios (tratamiento -> dosis en Actividades, y Actividades caído).
- Las pruebas crean sus propios usuarios (uno por rol, vía API), animales y recintos con nombres únicos, y limpian
  lo que la API permite borrar. Son independientes y no dependen del orden, así que corren en paralelo (`-n auto`).
  La prueba marcada `destructivo` detiene Actividades y lo vuelve a levantar; corre sola, después.
- Las fechas se calculan en `America/Guayaquil` (la base está en UTC) y nunca en el pasado.
- **Guardia**: `conftest.py` aborta si `GATEWAY_URL` no es `localhost` o `127.0.0.1` o si existe `DATABASE_URL` en
  el entorno. Las pruebas no tienen forma de apuntar a un servidor real.

Comandos locales (detalle y variantes para PowerShell en `03_pruebas/integracion/README.md`):

    cd 02_codigo_fuente/backend
    docker compose --env-file .env.test -f docker-compose.test.yml up -d --build --wait
    # cargar las variables de .env.test en la terminal, y luego:
    cd ../../03_pruebas/integracion
    pip install -r requirements-dev.txt
    pytest -m "not destructivo" -n auto
    pytest -m destructivo
    cd ../../02_codigo_fuente/backend
    docker compose --env-file .env.test -f docker-compose.test.yml down -v

## Pipeline de integración

`.github/workflows/integracion.yml`, solo en los PR hacia `test`:

1. Genera en el momento `SECRET_KEY`, contraseña de la base, y correo y contraseña del administrador de pruebas
   (`openssl rand`), los enmascara con `::add-mask::` y los exporta para esa corrida. No hay secretos en el repositorio.
2. Construye las cuatro imágenes **en paralelo** con `docker buildx bake` y caché de capas en GitHub Actions.
3. Levanta el entorno con `docker compose up --wait` y espera a que todo esté saludable.
4. Instala las dependencias de las pruebas (con caché de pip) y ejecuta `pytest -m "not destructivo" -n auto`
   (en paralelo) y después `pytest -m destructivo`.
5. Si algo falla, muestra `docker compose ps` y los logs. Siempre ejecuta `docker compose down -v`.

Usa `permissions: contents: read`, `timeout-minutes` y `concurrency` (cancela las ejecuciones obsoletas del mismo PR).
**No** forma parte del job `resultado` de `ci.yml`: ese workflow también corre en PR hacia `develop` y en push, donde
la integración no aplica. Se exige como check propio (`integracion`) en la protección de la rama `test`.

## Criterios de aceptación

- Todas las pruebas que se definan, unitarias y de integración, deben pasar.
- Cobertura mínima en código nuevo: **80 %** (se valida en SonarQube, ver `quality_gates.md`).
- Todo servicio nuevo debe incluir pruebas unitarias, su `GET /health` y, si tiene base de datos, `GET /health/ready`;
  y sus rutas se cubren en las pruebas de integración.

## Frontend (TypeScript)

<!-- TODO: Hacer la estrategia de pruebas del frontend usando Jest -->

(Por definir: framework de pruebas, por ejemplo Vitest o Jest, y su reporte `lcov`
para SonarQube.)

## Datos de prueba

- No se usan datos reales ni secretos en las pruebas.
- Las credenciales del entorno de integración **no están escritas en ningún archivo versionado**: el pipeline las
  genera al azar en cada ejecución y, en local, salen de un `.env.test` propio (ignorado por git) hecho a partir de
  `.env.test.example`. La base de datos solo existe mientras corre el entorno.
