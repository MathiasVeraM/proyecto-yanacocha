from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from src.config import DATABASE_URL

# El servidor de la base corta sin aviso las conexiones que quedan inactivas un tiempo.
# - pool_recycle: se descartan las conexiones con más de ~5 min en vez de reutilizarlas
# - keepalives: la conexión envía señales periódicas para que no se considere inactiva
# - pool_pre_ping y connect_timeout: si aun así una conexión falla, se detecta rápido
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=280,
    connect_args={
        "connect_timeout": 5,
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 3,
    },
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
