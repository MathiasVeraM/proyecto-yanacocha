# Servicio de Gestión Animal

Microservicio de fichas de ejemplares (HU-02): registro de animales con código automático, catálogo de taxonomía
(con sugerencias de iNaturalist), recintos, diagnósticos y tratamientos.

- Puerto: **8002** · Prefijo: **`/api/animales`** · Esquema de base de datos: **`gestion_animal`**
- Módulo que exige el gateway: `servicio-gestion-animal` ("Fichas de ejemplares")

## ⚠️ Avisos para el equipo (leer al traer estos cambios)

1. **Configuración de servicios**: el gateway usa `GESTION_ANIMAL_SERVICE_URL="http://localhost:8002"`.
   Gestión Animal usa `ACTIVIDADES_SERVICE_URL="http://localhost:8004"` para generar las dosis por medio
   de la conexión interna; en despliegues con contenedores debe apuntar al host del servicio de Actividades.
2. **Base de datos**: ejecutar en orden los scripts de `sql/` que aún no se hayan aplicado. Para los tratamientos,
   ejecutar `07_tratamientos_y_medicamentos.sql` después del esquema inicial; conserva el texto previo como
   descripción y deja sin conversión implícita las frecuencias y dosis antiguas.
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
  `genero`, `familia`, `orden`, `clase`, `id_inaturalist`), la tabla `AnimalImagen` (foto del ejemplar) y las
  relaciones `Animal → Taxonomia` y `Animal → Recinto`. Las columnas `nombre_comun`, `especie`, `genero` y
  `familia` salen de `Animal` (ahora viven en `Taxonomia`) y `Animal` gana `nombre` (nombre propio del ejemplar).
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

## Organización del código

Las fichas y fotografías de animales, los diagnósticos y los tratamientos se mantienen separados por modelo
y router (`animal_model.py` / `animal_routes.py`, `diagnostico_model.py` / `diagnostico_routes.py` y
`tratamiento_model.py` / `tratamiento_routes.py`). Sus servicios y repositorios también están separados;
las rutas públicas se mantienen bajo el prefijo `/api/animales`.

## Endpoints principales

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/animales?buscar=&clase=&id_taxonomia=&estado=&id_recinto=` | Lista con filtros combinables (`clase`: Mammalia, Aves, Reptilia…) |
| POST | `/api/animales` | Registra un animal; el código (`YC-2026-0001`…) se genera solo |
| GET / PUT | `/api/animales/{id}` | Ficha del animal / editarla (el código no cambia; se puede corregir la taxonomía) |
| GET | `/api/animales/taxonomia/sugerencias?buscar=` | Autocompletado: catálogo propio + iNaturalist |
| POST | `/api/animales/taxonomia/importar` | Guarda en el catálogo una especie de iNaturalist |
| GET / POST / PUT | `/api/animales/taxonomia` | Catálogo de especies |
| GET / POST / PUT | `/api/animales/recintos` | Recintos |
| PUT | `/api/animales/{id}/imagen` | Sube o reemplaza la foto (archivo JPG, PNG o WEBP, máx. 5 MB) |
| GET | `/api/animales/{id}/imagen` | Descarga la foto (exige token, como todo el servicio) |
| GET / POST | `/api/animales/{id}/diagnosticos` | Historial clínico |
| PUT | `/api/animales/diagnosticos/{id}` | Corregir un diagnóstico |
| GET | `/api/animales/{id}/signos-vitales` | Historial de signos vitales ordenado por fecha del diagnóstico |
| GET | `/api/animales/metricas/animales-con-tratamiento-en-curso` | Cantidad de animales distintos con al menos un tratamiento en curso |
| GET / POST | `/api/animales/diagnosticos/{id}/tratamientos` | Tratamientos de un diagnóstico |
| PUT | `/api/animales/tratamientos/{id}` | Editar o finalizar un tratamiento |
| POST | `/api/animales/tratamientos/{id}/generar-actividades` | Sincronizar las dosis programadas del tratamiento |

Cada tratamiento incluye una descripción, fecha de inicio y fin opcional, frecuencia en horas o días y hora
de inicio. Puede registrar cero o más medicamentos, cada uno con dosis positiva en ml. Las actividades de las
dosis se generan en el servicio de Actividades al guardar y se pueden renovar desde Planificación.

### Código del animal
Formato `YC-AAAA-NNNN`: prefijo de Yanacocha, año local de Ecuador y correlativo anual con al menos cuatro dígitos
(por ejemplo, `YC-2026-0001`). El correlativo se comparte entre todas las especies y el código no cambia si se corrige
la taxonomía del animal.

### Fotografía
Se sube como archivo y se guarda en la base de datos (tabla `animal_imagen`, una por animal), así se respalda con
el resto de los datos y no depende del disco del servidor. El tipo se valida por el contenido del archivo, no por
su extensión. `url_imagen` la llena el servicio al subir la foto (no se puede escribir a mano).

### Taxonomía e iNaturalist
Las sugerencias combinan el catálogo propio con la API pública y gratuita de [iNaturalist](https://www.inaturalist.org)
(en español, solo especies animales). Al elegir una sugerencia de iNaturalist se guarda en el catálogo con su
clase, orden, familia y género. El catálogo hace de caché: `id_inaturalist` es único, así que una especie no se
importa dos veces; si `id_inaturalist` está vacío, la especie se cargó a mano.
Si iNaturalist no responde en 3 segundos, se devuelve solo el catálogo y el registro sigue funcionando.
