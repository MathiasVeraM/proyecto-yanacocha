# SECRETOS Y VARIABLES

<div style="background-color: #0f0f0f; border-left: 4px solid #da093d; padding: 12px 16px; border-radius: 4px; font-family: monospace;">
  <b>Regla</b>: en este documento solo se registran <b>nombres y propósito</b>
  Los valores nunca se escriben en el repositorio, ni en documentos, issues o PRs.
</div>

## Manejo de Secretos

Los datos vulnerables para la ejecucion del pipeline, al menos hasta la integracion continua, se deben registrar y mantener como variables de entorno en el repositorio de Github, para que solo los administradores puedan ver o modificarlos:

GitHub → repositorio → *Settings → Secrets and variables → Actions*.
Solo los administradores del repositorio pueden verlos o modificarlos.

<!-- TODO: Agregar los secretos necesarios para despliegue (entrega continua) -->

| Nombre | Para qué sirve | Usado en | Fase |
|---|---|---|---|
| `SONAR_TOKEN` | Autentica el análisis en SonarQube Cloud | `ci.yml` | CI |
| `WEBHOOK_URL` | Envía avisos de fallos al canal del equipo | `ci.yml`, `deploy.yml` | CI |
| `DOCKERHUB_USERNAME` | Usuario de Docker Hub | `deploy.yml` | CD |
| `DOCKERHUB_TOKEN` | Token de acceso para subir imágenes | `deploy.yml` | CD |
| `GITLEAKS_LICENSE` | Licencia de Gitleaks (solo si el repo está en una organización) | `security.yml` | CI |

`GITHUB_TOKEN` lo crea GitHub automáticamente en cada ejecución; no hay que configurarlo.

Valores no sensibles como el archivo de `sonar.projectKey`, `sonar.organization` y la version de python o las imagenes que se usen se pueden guardar en los archivos necesarios del repositorio como `sonar-project.properties` y en el pipeline.

## Buenas prácticas
- Cada token con los **permisos mínimos** (el de Docker Hub, solo lectura y escritura del repositorio de imágenes).
- Los secretos no están disponibles en PRs que vienen de forks; el pipeline está pensado para ramas del mismo repositorio.
- Gitleaks revisa cada PR para detectar secretos subidos por error.
- Las credenciales del entorno de integración son valores de prueba definidos en `docker-compose.test.yml`; nunca credenciales reales.
- Rotar los tokens cuando cambie un integrante con acceso (al ser proyecto academico no se llevará a cabo)
- Si un secreto se filtra: (1) revocarlo de inmediato en el servicio de origen, (2) generar uno nuevo y actualizarlo en GitHub, (3) retirarlo del historial si llegó a un commit. Ver `runbook.md`.
