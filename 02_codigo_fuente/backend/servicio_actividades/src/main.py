from fastapi import Depends, FastAPI

from src.api.actividades_routes import router as actividades_router
from src.api.alimentaciones_routes import router as alimentaciones_router
from src.api.completar_actividad_routes import router as completar_actividad_router
from src.api.dietas_routes import router as dietas_router
from src.api.enriquecimientos_routes import router as enriquecimientos_router
from src.api.entrenamientos_routes import router as entrenamientos_router
from src.api.limpiezas_routes import router as limpiezas_router
from src.api.observaciones_routes import router as observaciones_router
from src.api.tomas_alimentacion_routes import router as tomas_alimentacion_router
from src.api.tratamientos_routes import router as tratamientos_router
from src.logica_negocio.auth import verificar_token_access

app = FastAPI(title="Servicio de Actividades - Yanacocha", version="1.0.0")

app.include_router(dietas_router)
app.include_router(alimentaciones_router)
app.include_router(enriquecimientos_router)
app.include_router(entrenamientos_router)
app.include_router(limpiezas_router)
app.include_router(tomas_alimentacion_router)
app.include_router(tratamientos_router)
# Antes de actividades_router: /observaciones no debe caer en /{id_actividad}.
app.include_router(observaciones_router)
app.include_router(actividades_router)
app.include_router(completar_actividad_router)


@app.get("/", dependencies=[Depends(verificar_token_access)])
def root():
    return {"message": "Servicio de Actividades operativo"}
