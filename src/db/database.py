from sqlmodel import SQLModel, create_engine

from src.config import settings


def get_engine():
    if not settings.database_url:
        return None
    # Use psycopg3 driver
    url = settings.database_url.replace("postgresql://", "postgresql+psycopg://")
    return create_engine(url, echo=settings.debug)


engine = get_engine()


def create_db_tables():
    if engine:
        SQLModel.metadata.create_all(engine)
