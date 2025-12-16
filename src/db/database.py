from sqlmodel import SQLModel, create_engine

from src.config import settings


def get_engine():
    if not settings.database_url:
        return None
    # Use psycopg3 driver
    url = settings.database_url.replace("postgresql://", "postgresql+psycopg://")
    return create_engine(
        url,
        echo=settings.debug,
        pool_pre_ping=True,  # Test connections before use (handles Neon drops)
        pool_recycle=300,  # Recycle connections every 5 minutes
        pool_size=5,
        max_overflow=10,
    )


engine = get_engine()


def create_db_tables():
    if engine:
        SQLModel.metadata.create_all(engine)
