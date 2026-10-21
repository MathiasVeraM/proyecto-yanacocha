# Servicio de Gestión Animal

Microservicio de fichas de ejemplares (HU-02): registro de animales con código automático, catálogo de taxonomía
(con sugerencias de iNaturalist), recintos, diagnósticos y tratamientos.

- Puerto: **8002** · Prefijo: **`/api/animales`** · Esquema de base de datos: **`gestion_animal`**
- Módulo que exige el gateway: `servicio-gestion-animal` ("Fichas de ejemplares")

## ⚠️ Avisos para el equipo (leer al traer estos cambios)

1. **El gateway necesita una variable nueva** en su `.env`:
   `GESTION_ANIMAL_SERVICE_URL="http://localhost:8002"` (si falta, usa ese valor por defecto).
2. **Base de datos**: los scripts de `sql/` ya se ejecutaron en el servidor. Solo hay que correrlos, en orden,
   si se monta una base nueva: `01_esquema_gestion_animal.sql`, `02_taxonomia_y_recintos.sql` y
   `03_imagen_animal.sql`.
3. **El servidor de PostgreSQL está en hora UTC** (5 horas adelante de Ecuador). Este servicio guarda las
   fechas en hora de Ecuador desde Python; otros servicios que usen `NOW()` o `CURRENT_DATE` quedarán adelantados
   (por ejemplo `usuario.fecha_creacion` en accesos).
4. **Conexiones que se cortan por inactividad**: el servidor cierra sin aviso las conexiones quietas. Si un
   servicio responde 504 en la primera petición tras un rato sin uso, conviene configurar su `create_engine`
   como en `src/database.py` de este servicio (`pool_pre_ping`, `pool_recycle` y keepalives).
5. **Ningún animal se elimina** (criterio de la HU-02): no hay DELETE; las salidas cambian `estado_actual`
   a `liberado`, `trasladado` o `fallecido`.

## 📌 Pendientes

- [ ] **Actualizar el diagrama ER**: agregar la tabla `Taxonomia` (`id_taxonomia`, `nombre_comun`, `especie`,
  `genero`, `familia`, `id_inaturalist`) y las relaciones `Animal → Taxonomia` y `Animal → Recinto`. Las columnas
  `nombre_comun`, `especie`, `genero` y `familia` salen de `Animal` (ahora viven en `Taxonomia`).
- [ ] **Probar el registro completo con datos reales** desde el frontend (crear un recinto, elegir la especie y
  registrar un animal). Ojo: lo que se registre **no se puede borrar**, así que conviene usar datos reales del
  centro y no de prueba.

## Cómo levantarlo

```bash
cd 02_codigo_fuente/backend/servicio_gestion_animal
python -m venv venv
venv\Scripts\activate            # Windows (en Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
cp .env.example .env             # y completar DATABASE_URL y SECRET_KEY (la misma de accesos y del gateway)
uvicorn src.main:app --reload --port 8002
```

Documentación interactiva de los endpoints: <http://localhost:8002/docs>

Pruebas (usan SQLite en memoria y un iNaturalist simulado: no tocan la base real ni internet):

```bash
pytest --cov=src
```

## Endpoints principales

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/animales?buscar=&id_taxonomia=&estado=&id_recinto=` | Lista con filtros combinables |
| POST | `/api/animales` | Registra un animal; el código (`TO-001`, `CLF-002`…) se genera solo |
| GET / PUT | `/api/animales/{id}` | Ficha del animal / editarla (código y especie no se editan) |
| GET | `/api/animales/taxonomia/sugerencias?buscar=` | Autocompletado: catálogo propio + iNaturalist |
| POST | `/api/animales/taxonomia/importar` | Guarda en el catálogo una especie de iNaturalist |
| GET / POST / PUT | `/api/animales/taxonomia` | Catálogo de especies |
| GET / POST / PUT | `/api/animales/recintos` | Recintos |
| PUT | `/api/animales/{id}/imagen` | Sube o reemplaza la foto (archivo JPG, PNG o WEBP, máx. 5 MB) |
| GET | `/api/animales/{id}/imagen` | Descarga la foto (exige token, como todo el servicio) |
| GET / POST | `/api/animales/{id}/diagnosticos` | Historial clínico |
| PUT | `/api/animales/diagnosticos/{id}` | Corregir un diagnóstico |
| GET / POST | `/api/animales/diagnosticos/{id}/tratamientos` | Tratamientos de un diagnóstico |
| PUT | `/api/animales/tratamientos/{id}` | Editar o finalizar un tratamiento |

### Código del animal
Iniciales del nombre científico + número correlativo por iniciales: *Canis lupus familiaris* → `CLF-001`,
`CLF-002`…; *Tremarctos ornatus* → `TO-001`. Especies con las mismas iniciales comparten el contador.

### Fotografía
Se sube como archivo y se guarda en la base de datos (tabla `animal_imagen`, una por animal), así se respalda con
el resto de los datos y no depende del disco del servidor. El tipo se valida por el contenido del archivo, no por
su extensión. `url_imagen` la llena el servicio al subir la foto (no se puede escribir a mano).

### Taxonomía e iNaturalist
Las sugerencias combinan el catálogo propio con la API pública y gratuita de [iNaturalist](https://www.inaturalist.org)
(en español, solo especies animales). Al elegir una sugerencia de iNaturalist se guarda en el catálogo.
Si iNaturalist no responde en 3 segundos, se devuelve solo el catálogo y el registro sigue funcionando.
