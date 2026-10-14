# PLAN GENERAL

## 1. Objetivo
Automatizar la verificación de calidad y seguridad del código en cada cambio,
para detectar errores antes de llegar a producción, rama `main`.

## 2. Alcance

El alcance para las pruebas se contempla realizar: pruebas unitarias, de integración en la rama test, y análisis de código estático utilizando SonarQube Cloud, CodeQL, Gitleaks para análisis de seguridad.

- Backend en Python, organizado por servicios en `02_codigo_fuente/backend/<servicio o gateway>`.
- Frontend en TypeScript, cuyo código en general vive en `02_codigo_fuente/frontend/`.

## 3. Herramientas
| Necesidad | Herramienta |
|---|---|
| Automatización | GitHub Actions |
| Pruebas unitarias | pytest, pytest-cov |
| Pruebas de integración | pytest + Docker Compose (dentro del runner) |
| Análisis estático y cobertura | SonarQube Cloud |
| Seguridad | CodeQL, Gitleaks, Dependabot |
| Imágenes | Docker (multi-stage), Docker Hub |

## 4. Flujo general

Las ramas siguen un flujo único, definido en `estrategia_ramas.md`:

    feature/*  →  develop  →  test  →  main

- Todo cambio entra por Pull Request, con aprobación y checks obligatorios.
- `develop` integra el trabajo del equipo.
- `test` es la verificación previa a producción, con pruebas de integración.
- `main` es el código en producción.

Workflows (en `.github/workflows/`):

| Archivo | Función |
|---|---|
| `ci.yml` | Orquesta tests, SonarQube y notificaciones en cada PR y push |
| `_backend-tests.yml` | Pytest por servicio (matriz) con reporte de cobertura |
| `_frontend-tests.yml` | Lint, tipos y pruebas del frontend |
| `integracion-tests.yml` | Pruebas de integración con Docker Compose |
| `security.yml` | CodeQL y Gitleaks |
| `dependabot.yml` | Actualización de dependencias (en `.github/`) |

<!-- TODO: Agregar las descripciones para workflow de despliegue -->

## 5. Qué corre en cada etapa

| Evento | Unitarias | SonarQube | Seguridad | Integración | Despliegue |
|---|---|---|---|---|---|
| PR hacia `develop` | ✅ | ✅ | ✅ | ❌ | ❌ |
| PR hacia `test` | ✅ | ✅ | ✅ | ✅ | ❌ |
| PR hacia `main` | ✅ | ✅ | ✅ | ✅ | ❌ |
| Merge a `main` | ✅ | ✅ | ✅ | ✅ | ✅ (fase CD) |

Detalle de cada nivel en `estrategia_pruebas.md`; criterios de aprobación en `quality_gates.md`.

## 6. Notificaciones

<!-- TODO: Investigar las formas de notificación con Github Actions -->
| Canal | Qué avisa | Quién lo recibe |
|---|---|---|
| GitHub (correo y web) | Checks fallidos en un PR | Autor del PR |
| SonarQube Cloud | Quality Gate fallido, comentario en el PR | Autor y revisores |
| Canal del equipo (webhook) | Fallos del pipeline | Todo el equipo | 
| Alertas de Dependabot y CodeQL | Vulnerabilidades | Administradores del repo |
