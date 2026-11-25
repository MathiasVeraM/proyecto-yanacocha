# Pruebas de integración

Pruebas por **HTTP real** contra el gateway del `docker-compose.test.yml` (gateway, los tres servicios y una
base PostgreSQL efímera, en memoria). No hay mocks. Viven fuera de `02_codigo_fuente/backend/` a propósito: el
workflow de pruebas unitarias descubre las carpetas de ese directorio y las correría por error.

| Archivo | Área |
|---|---|
| `test_a_salud.py` | `/health` y `/health/ready` de todos los servicios, puertos publicados y endurecimiento de contenedores |
| `test_b_autenticacion.py` | login, tokens inválidos o vencidos (401), módulo no permitido (403), rutas no mapeadas |
| `test_c_permisos_rol.py` | qué puede hacer cada rol (Veterinaria, Manejo de Animales, Voluntarios, administrador) |
| `test_d_gestion_animal.py` | taxonomía, recintos, animales (`YC-AAAA-NNNN`), diagnósticos y tratamientos |
| `test_e_actividades.py` | crear, listar, calendario, completar, reabrir, duplicados, cruces y observaciones |
| `test_f_dietas_tomas.py` | dietas y tomas de alimentación |
| `test_g_integracion_servicios.py` | tratamiento -> dosis en Actividades, y Actividades caído |

## Seguridad: nunca contra un entorno real

`conftest.py` aborta antes de la primera prueba si:

- `GATEWAY_URL` no apunta a `localhost` o `127.0.0.1`;
- existe `DATABASE_URL` en el entorno (estas pruebas solo usan HTTP y no necesitan la base);

## Cómo correrlas en local

Desde `02_codigo_fuente/backend`, con un `.env.test` propio (copia de `.env.test.example` con valores aleatorios;
ver el encabezado de ese archivo):

```bash
docker compose --env-file .env.test -f docker-compose.test.yml up -d --build --wait
```

Cargar las variables y ejecutar (Git Bash):

```bash
set -a; . ./.env.test; set +a
cd ../../03_pruebas/integracion
python -m venv venv && . venv/Scripts/activate      # en Linux/macOS: . venv/bin/activate
pip install -r requirements-dev.txt
pytest -m "not destructivo" -n auto                 # el grueso, en paralelo
pytest -m destructivo                               # detiene y vuelve a levantar Actividades; va solo
```

En PowerShell, en lugar de `set -a`:

```powershell
Get-Content .env.test | ForEach-Object { if ($_ -match '^\s*([^#=\s]+)=(.*)$') { Set-Item "env:$($Matches[1])" $Matches[2] } }
```

Al terminar (borra la base, que no tiene volumen):

```bash
docker compose --env-file .env.test -f docker-compose.test.yml down -v
```

## Notas

- **Marcadores**: `lento` (muchos registros), `requiere_docker` (usa `docker exec`/`inspect`; se omite sin Docker)
  y `destructivo` (detiene un contenedor; no debe correr junto a otras pruebas).
- **Fechas**: siempre en `America/Guayaquil`, como los servicios (la base está en UTC), y nunca en el pasado.
  Para completar una actividad (solo hoy o antes) se usa una limpieza de hoy sin hora.
- **Independencia**: cada prueba crea su animal y su recinto con nombres únicos. Lo que la API permite borrar se
  limpia al terminar (actividades, dietas finalizadas, usuarios desactivados); el resto desaparece con la base.
- `SECRET_KEY` es opcional: solo hace falta para la prueba del token vencido (se omite si no está).
- **Si cambias el `.env.test`**, recrea el entorno (`down -v` y `up -d --build --wait`) y vuelve a cargar las variables:
  el administrador se crea una sola vez al levantar la base, con los valores de ese momento. Si no coinciden, las
  pruebas se detienen al inicio con un aviso (HTTP 401 al iniciar sesión).
