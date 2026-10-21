from fastapi import FastAPI
from src.api.recinto_routes import router as recintos_router
from src.api.routes import router as animales_router
from src.api.taxonomia_routes import router as taxonomia_router

app = FastAPI(title="Servicio de Gestión Animal - Yanacocha", version="1.0.0")

# Taxonomía y recintos van antes que animales: si no, /api/animales/recintos
# se interpretaría como /api/animales/{id_animal}
app.include_router(taxonomia_router)
app.include_router(recintos_router)
app.include_router(animales_router)

@app.get("/")
def root():
    return {"message": "Servicio de Gestión Animal operativo"}
