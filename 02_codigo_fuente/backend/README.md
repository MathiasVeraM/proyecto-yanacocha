# Backend - Yanacocha

Microservicios FastAPI (Python 3.12) detrás de un API Gateway. Una sola base PostgreSQL con tres esquemas
(`public`, `gestion_animal`, `actividades`).

| Carpeta | Puerto | Qué hace |
|---|---|---|
| `gateway/` | 8000 | Único punto de entrada: valida el JWT, controla acceso por módulo y rol, y reenvía a los servicios |
| `servicio_accesos/` | 8001 | Login, usuarios, roles, módulos y permisos (esquema `public`) |
| `servicio_gestion_animal/` | 8002 | Taxonomía, recintos, animales, diagnósticos y tratamientos. Llama por HTTP a Actividades para generar las dosis (`ACTIVIDADES_SERVICE_URL`) |
| `servicio_actividades/` | 8003 | Actividades, dietas, tomas, dosis de tratamientos y observaciones. Lee tablas de los otros esquemas |

## Variables de entorno

Cada servicio lee su propio `.env` (hay un `.env.example` en cada carpeta). Reglas:

- La **misma `SECRET_KEY`** en el gateway y en los tres servicios.
- El gateway necesita las URLs de los servicios: `ACCESSOS_SERVICE_URL` (con doble S, así se llama en el código),
  `GESTION_ANIMAL_SERVICE_URL` y `ACTIVIDADES_SERVICE_URL`. Gestión Animal también usa `ACTIVIDADES_SERVICE_URL`.
- Los servicios con base de datos necesitan `DATABASE_URL` (`postgresql://usuario:clave@host:5432/base`).
- Los `.env` no se suben al repositorio (`.gitignore`). Nunca se escriben secretos en Dockerfiles, compose ni workflows.

El `.env.example` de **esta carpeta** solo cubre lo que lee `docker-compose.yml` (puerto del gateway y, para la
base local opcional, `POSTGRES_PASSWORD`).

## Dependencias

Cada servicio tiene dos archivos con versiones fijadas:

- `requirements.txt`: solo lo que necesita para ejecutarse (lo que entra en la imagen Docker).
- `requirements-dev.txt`: empieza con `-r requirements.txt` y agrega pytest, pytest-cov y el cliente que usa `TestClient`.

```bash
pip install -r requirements-dev.txt     # para trabajar y probar
```

## Levantar todo con Docker

Requisitos: Docker con Compose v2 y los cuatro `.env` (gateway y los tres servicios). Desde esta carpeta:

```bash
docker compose up -d --build --wait     # construye, levanta y espera a que todo esté saludable
curl http://127.0.0.1:8000/health       # {"status":"ok"}
docker compose down
```

- `docker-compose.yml` **no incluye base de datos**: cada servicio usa el `DATABASE_URL` de su `.env`.
- El gateway es lo único que publica un puerto (`127.0.0.1:8000`). En un servidor, para aceptar conexiones externas,
  define `GATEWAY_BIND_ADDRESS=0.0.0.0` (y opcionalmente `GATEWAY_PORT`) en el `.env` de esta carpeta.
- Dentro de Docker los servicios se llaman por nombre (`http://accesos:8001`, ...); el compose reemplaza las URLs
  de los `.env`, que pueden seguir diciendo `localhost`.

### Con una base de datos local y limpia (sin tocar la real)

```bash
cp .env.example .env                    # completar POSTGRES_PASSWORD (solo letras y números)
docker compose -f docker-compose.yml -f docker-compose.local-db.yml up -d --build --wait
```

Agrega PostgreSQL 17 con volumen, ejecuta en orden los scripts SQL de cada servicio (`db-init.sh`) y crea el primer
administrador con `ADMIN_CORREO` y `ADMIN_PASSWORD` de `servicio_accesos/.env`. `down -v` borra los datos.

## Endpoints de salud

Sin autenticación y sin datos sensibles.

| Ruta | Dónde | Qué comprueba |
|---|---|---|
| `GET /health` | gateway y los tres servicios | El proceso está vivo (liveness) |
| `GET /health/ready` | los tres servicios | La base de datos responde a un `SELECT 1`; 503 si no |

El gateway solo tiene liveness: si un servicio cae, el gateway sigue vivo y responde 503 en esas rutas.
`/health` está fuera de `mapa_rutas.py`, así que el gateway sigue rechazando cualquier ruta que no conoce.
Los `/health` de los servicios son internos: no se alcanzan por el gateway.

## Imágenes Docker

Cada servicio tiene su `Dockerfile` multi-stage (`python:3.12-slim` con versión fija):

| Etapa | Para qué |
|---|---|
| `builder` | Construye las wheels de `requirements.txt` |
| `test` | Instala `requirements-dev.txt` y corre pytest dentro de un contenedor |
| `runtime` | Imagen final: solo `src/` (y `crear_admin.py` en accesos), usuario no root, sin compiladores ni secretos |

```bash
docker build -t yanacocha-gateway ./gateway                                    # imagen final
docker build --target test -t yanacocha-gateway-test ./gateway && docker run --rm yanacocha-gateway-test
```

Los scripts `sql/` no entran en las imágenes: `docker-compose` los monta en solo lectura.

## Pruebas

**Unitarias** (sin Docker, con dependencias simuladas), por servicio:

```bash
cd gateway            # o servicio_accesos, servicio_gestion_animal, servicio_actividades
pytest
```

**Integración** (HTTP real contra los contenedores y una base PostgreSQL efímera): viven en
[`03_pruebas/integracion/`](../../03_pruebas/integracion/README.md), fuera de esta carpeta a propósito, porque el
workflow de pruebas unitarias descubre cada carpeta de `backend/` como un servicio. Se levantan con
`docker-compose.test.yml` (independiente del compose de desarrollo: base en memoria, solo el gateway publica puerto,
`no-new-privileges`, `cap_drop: ALL`, `read_only`). Hay un `.env.test.example` con los nombres de variables.

Comandos completos para correrlas en local: ver el README de `03_pruebas/integracion/`.
En el pipeline corren con `.github/workflows/integracion.yml` (ver `04_despliegue_ci_cd/`).

> No agregues carpetas nuevas dentro de `backend/` que no sean servicios: `_backend-tests.yml` crea un job por carpeta.
