# proyecto-yanacocha
Proyecto de titulación capstone. Sistema de gestión de información y procesos del centro de rescate yanacocha utilizando FastAPI y Vue.

## ⚠️ Avisos
- **Servicio de gestión animal** (puerto 8002): avisos para el equipo y pendientes (diagrama ER, prueba con
  datos reales) en [02_codigo_fuente/backend/servicio_gestion_animal/README.md](02_codigo_fuente/backend/servicio_gestion_animal/README.md).
  El `.env` del gateway necesita `GESTION_ANIMAL_SERVICE_URL`.

## Backend con Docker y pruebas

- Levantar gateway y servicios con un solo comando, variables de entorno y base local opcional:
  [02_codigo_fuente/backend/README.md](02_codigo_fuente/backend/README.md).
- Pruebas de integración (HTTP real contra contenedores y una base efímera):
  [03_pruebas/integracion/README.md](03_pruebas/integracion/README.md).
- Pipeline y estrategia de pruebas: [04_despliegue_ci_cd/](04_despliegue_ci_cd/README.md).

