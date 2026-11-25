# syntax=docker/dockerfile:1
# API Gateway - Yanacocha (puerto 8000). Contexto de construcción: esta carpeta.
#   Imagen final:  docker build -t yanacocha-gateway .
#   Pruebas:       docker build --target test -t yanacocha-gateway-test . && docker run --rm yanacocha-gateway-test
# No lleva secretos: SECRET_KEY y las URLs de los servicios se inyectan al ejecutar el contenedor.

ARG PYTHON_IMAGE=python:3.12.12-slim-bookworm

# ---------- Etapa base: valores comunes ----------
FROM ${PYTHON_IMAGE} AS base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app
WORKDIR /app

# ---------- Etapa builder: compila las dependencias de ejecución en wheels ----------
FROM base AS builder
COPY requirements.txt .
RUN pip wheel --wheel-dir /wheels -r requirements.txt

# ---------- Etapa test: solo para correr pytest dentro de un contenedor (no es la imagen final) ----------
FROM base AS test
COPY requirements.txt requirements-dev.txt ./
RUN pip install -r requirements-dev.txt
COPY pytest.ini ./
COPY src ./src
COPY tests ./tests
USER app
CMD ["pytest", "-p", "no:cacheprovider"]

# ---------- Etapa runtime: imagen final (debe ser la última del archivo) ----------
FROM base AS runtime
COPY requirements.txt .
# Las wheels se montan desde builder: se instalan sin red y no quedan en ninguna capa
RUN --mount=type=bind,from=builder,source=/wheels,target=/wheels \
    pip install --no-index --find-links=/wheels -r requirements.txt
# Solo el código de la aplicación; pertenece a root, así que el usuario de ejecución no puede modificarlo
COPY src ./src
USER app
EXPOSE 8000

# Sin curl en la imagen slim: se usa Python. urlopen lanza excepción si la respuesta no es 2xx.
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"]

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
