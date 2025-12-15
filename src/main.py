from contextlib import asynccontextmanager

import logfire
from fastapi import FastAPI

from src.api.webhooks import router as webhook_router
from src.config import settings

if settings.logfire_token:
    logfire.configure(token=settings.logfire_token)
else:
    logfire.configure(send_to_logfire=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logfire.info("Starting PRB WA Agent")
    yield
    logfire.info("Shutting down PRB WA Agent")


app = FastAPI(
    title="PRB WA Agent",
    description="WhatsApp AI agent for PRB team operations",
    version="0.1.0",
    lifespan=lifespan,
)

logfire.instrument_fastapi(app)

app.include_router(webhook_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
