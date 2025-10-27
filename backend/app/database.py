from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from redis import Redis, ConnectionPool
from .config import settings

# --- PostgreSQL Setup ---
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Redis Setup ---
redis_pool = ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True)

def get_redis_client():
    """Dependency to get a Redis client from the connection pool."""
    return Redis(connection_pool=redis_pool)

Base = declarative_base()
