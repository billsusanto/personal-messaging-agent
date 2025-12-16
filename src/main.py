from contextlib import asynccontextmanager

import logfire
from fastapi import FastAPI

from src.api.webhooks import router as webhook_router
from src.config import settings
from src.db.database import create_db_tables
from src.db.models import AgentAction, ApprovalQueue, Message  # noqa: F401

if settings.logfire_token:
    logfire.configure(token=settings.logfire_token)
else:
    logfire.configure(send_to_logfire=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logfire.info("Starting Personal Messaging Agent")
    create_db_tables()
    logfire.info("Database tables ready")
    yield
    logfire.info("Shutting down Personal Messaging Agent")


app = FastAPI(
    title="Personal Messaging Agent",
    description="WhatsApp AI agent for personal messaging operations",
    version="0.1.0",
    lifespan=lifespan,
)

logfire.instrument_fastapi(app)

app.include_router(webhook_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
