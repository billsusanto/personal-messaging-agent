from sqlmodel import SQLModel, create_engine

from src.config import settings

engine = create_engine(settings.database_url, echo=settings.debug) if settings.database_url else None


def create_db_tables():
    if engine:
        SQLModel.metadata.create_all(engine)
