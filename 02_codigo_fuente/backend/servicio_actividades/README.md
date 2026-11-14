# Servicio de Actividades

Microservicio de planificación del Centro de Rescate de Fauna Silvestre: dietas, tomas de alimentación,
enriquecimientos, entrenamientos y limpieza de recintos.

- Prefijo API: **`/api/actividades`**
- Esquema PostgreSQL: **`actividades`**
- Módulo: `servicio-actividades`

## Configuración

Copie `.env.example` a `.env` y defina `DATABASE_URL` y `SECRET_KEY`. La clave debe coincidir con
la del servicio de accesos y el gateway. `ALGORITHM` usa `HS256` por defecto.
`HORIZONTE_TOMAS_DIAS` determina el máximo de días para tomas de alimentación (30 por defecto). Los tratamientos
usan un horizonte móvil de siete días.

## Base de datos

El servicio no crea tablas al arrancar. Antes de iniciar la API, ejecute manualmente los scripts `sql/` en orden.
`03_tratamientos.sql` requiere que exista `gestion_animal.tratamiento`, creado o actualizado por
`servicio_gestion_animal/sql/07_tratamientos_y_medicamentos.sql`.
`04_validaciones_actividades.sql` agrega el índice único que impide actividades duplicadas (ya aplicado en
la base compartida; se puede volver a ejecutar sin problema).

Los límites de fechas y duración (un año hacia adelante, 4 horas por actividad, 30 min por defecto para el
enriquecimiento, repeticiones de hasta 3 meses y dietas que empiezan hasta 30 días después) se configuran en
`.env` (ver `.env.example`) y el frontend los consulta en `GET /api/actividades/limites`.

## Instalar y levantar

```powershell
cd 02_codigo_fuente/backend/servicio_actividades
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn src.main:app --reload --port 8004
```

La documentación interactiva queda disponible en `http://localhost:8004/docs`.

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/actividades/dietas` | Asigna una dieta y reemplaza la vigente de forma transaccional |
| GET | `/api/actividades/animales/{id_animal}/dietas` | Historial de dietas |
| GET | `/api/actividades/animales/{id_animal}/dietas/vigente` | Dieta vigente |
| GET | `/api/actividades/dietas/{id_dieta}` | Consulta una dieta |
| POST | `/api/actividades/tomas/generar` | Genera tomas para una dieta hasta una fecha |
| POST | `/api/actividades/tomas/renovar` | Renueva el horizonte de todas las dietas vigentes |
| POST | `/api/actividades/tratamientos/{id_tratamiento}/generar` | Genera o sincroniza las dosis dentro de los siguientes siete días |
| POST | `/api/actividades/tratamientos/renovar` | Renueva el horizonte de tratamientos en curso |
| POST | `/api/actividades/alimentaciones` | Programa una toma vinculada a dieta |
| POST / GET | `/api/actividades/enriquecimientos` | Programa o consulta enriquecimientos |
| POST | `/api/actividades/entrenamientos` | Programa un entrenamiento |
| POST | `/api/actividades/limpiezas` | Programa limpieza de recinto, sin asociar animales |
| POST / GET | `/api/actividades` | Programa una actividad genérica o lista con filtros |
| GET | `/api/actividades/{id_actividad}` | Consulta una actividad |
| GET | `/api/actividades/calendario` | Consulta eventos para visualización |
| PATCH | `/api/actividades/{id_actividad}/completar` | Completa una actividad |

El servicio valida JWT y obtiene el identificador de usuario desde el token. Los roles y permisos
se aplican en el gateway y el servicio de accesos.

## Pruebas

```powershell
pytest --cov=src
```

Las pruebas de contrato usan SQLite en memoria; no requieren una base PostgreSQL.
