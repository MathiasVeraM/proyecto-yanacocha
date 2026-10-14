# RUNBOOK

En caso de existir algún error, el proceso es abrir el PR → pestaña *Checks* (o *Actions*) → entrar al job en rojo → leer el primer error, no el último. Casi siempre ahí está la causa.

## Fallos en el CI

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| Fallan los tests unitarios | Cambio que rompe una prueba o dependencia nueva | Reproducir en local: `pytest 02_codigo_fuente/backend/<servicio>`. Corregir y subir commit. |
| `ModuleNotFoundError` en CI pero no en local | Falta la dependencia en `requirements.txt` o `pythonpath` | Agregarla al `requirements.txt` del servicio; revisar `pytest.ini`. |
| Quality Gate de SonarQube en rojo | Cobertura baja, duplicación, bug o hotspot sin revisar | Abrir el enlace de SonarQube desde el PR, ver qué condición falla y corregir. Si es falso positivo, marcarlo con justificación. |
| Sonar muestra cobertura 0 % | No encuentra los reportes `coverage-*.xml` o las rutas no coinciden | Verificar que el job de tests sube el artefacto, que `sonar.python.coverage.reportPaths` apunta a él y que `sonar.sources` coincide con las rutas del XML. |
| Sonar: error de autenticación | `SONAR_TOKEN` ausente, vencido o inválido | Generar token nuevo en SonarQube y actualizar el secret. |
| Sonar: conflicto con "Automatic Analysis" | Está activo el análisis automático y el de Actions a la vez | Desactivar el análisis automático en el proyecto de SonarQube. |
| CodeQL reporta una alerta | Posible vulnerabilidad en el código | Revisar en *Security → Code scanning*. Corregir, o descartar con motivo si es falso positivo. |
| Gitleaks detecta un secreto | Credencial en un commit | Ver sección 4 (fuga de secretos). |
| Falla el PR de Dependabot | La nueva versión rompe algo | Leer el error; ajustar el código, o cerrar el PR y fijar la versión anterior. |
| Falla el título del PR | No sigue Conventional Commits | Editar el título (`feat:`, `fix:`, `docs:`...). |

## Fallos en pruebas de integración

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| `up --wait` se queda esperando o expira | Un contenedor no pasa su `healthcheck` | Ver el paso "Logs si algo falla" del job. Reproducir en local con `docker compose -f 02_codigo_fuente/docker-compose.test.yml up --build`. |
| Contenedor termina al arrancar | Error en el Dockerfile, variable de entorno faltante o dependencia | Revisar logs del servicio; probar la imagen en local. |
| `Connection refused` en las pruebas | Servicio aún no listo o puerto incorrecto | Confirmar `healthcheck` y los puertos en `docker-compose.test.yml` y en `conftest.py`. |
| Pasa en local pero falla en CI | Diferencias de entorno o datos previos | Usar `down -v` antes de probar en local para partir de cero; revisar versiones. |
| Pruebas que fallan a veces | Dependen del orden o de datos de otras pruebas | Hacer que cada prueba cree sus propios datos con nombres únicos. |

## Fuga de secretos
1. **Revocar** la credencial de inmediato en el servicio de origen.
2. Generar una nueva y actualizar el secret en GitHub.
3. Quitar el secreto del código. Si ya está en el historial, hay que limpiarlo
   (`git filter-repo`) o, en un proyecto académico, evaluar recrear la rama afectada.
4. Avisar al equipo y registrar el incidente.

## No puedo hacer merge

| Mensaje en el PR | Qué falta |
|---|---|
| "Review required" | Una aprobación de otro colaborador |
| Check pendiente o en rojo | Esperar o corregir el check obligatorio |
| "Conversations must be resolved" | Resolver los comentarios abiertos |
| "Branch is out of date" | Actualizar la rama con la base y esperar el pipeline |

No está permitido saltarse las reglas, ni siquiera siendo administrador.

## El pipeline está lento
- Revisar que el caché de dependencias esté activo (`cache: pip`, `cache: npm`).
- Confirmar que los filtros por ruta evitan correr servicios no modificados.
- Verificar que `concurrency` cancela corridas obsoletas.
- Revisar el tamaño de las imágenes Docker (multi-stage, `python:3.12-slim`).

## 8. Despliegue y rollback

<!-- TODO: Anotar el proceso para despliegue y rollback -->