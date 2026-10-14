# QUALITY GATES

## SonarQube Cloud y Otras Verificaciones

Para establecer los umbrales de calidad y realizar una evaluación de código nuevo cada vez que se realiza un PR a develop, test y main, utilizamos SonarQube Cloud conectandolo de esa manera y a través del pipeline con el repositorio. 

<div style="background-color: #0f0f0f; border-left: 4px solid #da093d; padding: 12px 16px; border-radius: 4px; font-family: monospace;">
    Los umbrales se revisan al cerrar cada fase del proyecto. Cualquier cambio se registra en este documento mediante un PR.
</div>

<!-- TODO: Revisar los umbrales y que hacer si falla -->

| Condición (código nuevo) | Umbral |
|---|---|
| Cobertura de pruebas | ≥ 80 % |
| Líneas duplicadas | ≤ 3 % |
| Fiabilidad (bugs) | Rating A |
| Seguridad (vulnerabilidades) | Rating A |
| Mantenibilidad | Rating A |
| Security hotspots revisados | 100 % |

Otras verificaciones de seguridad nos las darían las herramientas de CodeQL que nos sirve para detectar vulnerabilidades en el código, buscando no tener alertas de severidad alta o crítica. También utilizar Gitleaks para evitar subir contraseñas y datos sensibles al repositorio, con cero hallazgos. Y el uso de Dependabot para revisar las dependencias vulnerables, con las alertas altas o críticas atendidas antes de la rama `main`.

## Qué hacer si falla
1. Abrir el detalle del check (Actions o enlace de SonarQube desde el PR).
2. Corregir en la misma rama y subir el commit; el pipeline se repite solo.
3. Si es un falso positivo, marcarlo en SonarQube con justificación y avisar al revisor.
4. No se permite desactivar ni saltar el gate para hacer merge.