# ESTRATEGIA DE RAMAS

## Ramas y Flujo esperado

Para el proyecto estamos usando la estructura de gitflow con sus respectivas ramas, y creando nuevas para cada funcionalidad agregada o cambio que debamos realizar.

| Rama | Propósito | Quién escribe en ella |
|---|---|---|
| `main` | Código en producción | Solo por PR desde `test` |
| `test` | Verificación previa a producción (pruebas de integración) | Solo por PR desde `develop` |
| `develop` | Integración del trabajo del equipo | Solo por PR desde ramas de trabajo |
| `feature/*`, `fix/*`, `docs/*` | Trabajo individual | Cada desarrollador |

El flujo que se busca seguir es creando una nueva rama a partir de develop, agregar nueva funcionalidades y código y utilizar pull requests (PR) para unirle a la rama develop, manteniendo así la verdad en el gestor de cambios. Además, del despliegue de los cambios en el servidor.

<div style="background-color: #0f0f0f; border-left: 4px solid #da093d; padding: 12px 16px; border-radius: 4px; font-family: monospace;">
  feature/&lt;descripcion&gt; → develop → test → main (despliegue automático)
</div>

## Convenciones y Reglas de protección (develop, test y main)

- Las ramas siempre van a iniciar con el termino feature. Ejemplo: `feature/<descripcion>`. 
- Las ramas de trabajo se eliminan del repositorio en Github después de terminada las funcionalidades que se necesiten aplicar completamente (siendo revisadas por el docente guia).
- La rama `main` solo acepta PRs desde `test` (validado por un job del pipeline).
- Commits y títulos de PR siguen Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`...). Esto para generar el CHANGELOG correspondiente de los cambios de manera automática a futuro.
- PR obligatorio; sin push directo a las ramas.
- Mínimo 1 aprobación al crear PR; no puede ser el que crea el PR.
- Conversaciones resueltas antes del merge.
- Sin force push ni borrado de rama.
- Sin excepciones para administradores.

## Checks obligatorios por rama (develop, test y main)

| Check | `develop` | `test` | `main` | 
|---|---|---|---|
| Aprobación (1 mínimo) | SI | SI | SI | 
| Tests unitarios (pytest) | SI | SI | SI |
| SonarQube (Quality Gate) | SI | SI | SI |
| Seguridad (CodeQL, Gitleaks) | SI | SI | SI |
| Pruebas de integración | NO | SI | SI |
