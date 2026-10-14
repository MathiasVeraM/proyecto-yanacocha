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
| Seguridad | CodeQL, Gitleaks |
| Imágenes | Docker (multi-stage), Docker Hub |

## 4. Flujo general
(Resumen del flujo y referencia a `estrategia_ramas.md` y al diagrama.)

## 5. Qué corre en cada etapa
(Tabla PR / merge. Se completa tras definir ramas y pruebas.)

## 6. Notificaciones
(A quién y por qué canal se avisa de los fallos.)

## 7. Responsables y mantenimiento
(Quién mantiene el pipeline.)
