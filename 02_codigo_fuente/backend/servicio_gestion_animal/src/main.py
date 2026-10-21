from fastapi import FastAPI

app = FastAPI(title="Servicio de Gestión Animal - Yanacocha", version="1.0.0")

@app.get("/")
def root():
    return {"message": "Servicio de Gestión Animal operativo"}
