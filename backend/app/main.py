"""FastAPI application factory — CORS, lifespan, routers."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import init_db
from .api import runs, ws, interventions, reports, config_presets, loom, control


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(runs.router)
app.include_router(ws.router)
app.include_router(interventions.router)
app.include_router(reports.router)
app.include_router(config_presets.router)
app.include_router(loom.router)
app.include_router(control.router)


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}
