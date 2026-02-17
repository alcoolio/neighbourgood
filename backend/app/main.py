"""NeighbourGood API – main application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import status

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Community resource-sharing platform with crisis-mode support.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(status.router)
