"""Main FastAPI application for currency conversion API."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from currency_app.database import create_tables
from currency_app.routers import conversion, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup: Create database tables
    create_tables()
    yield
    # Shutdown: Could add cleanup here if needed


# Create FastAPI application
app = FastAPI(
    title="Currency Conversion API",
    description="A demo API for currency conversion with debugging capabilities",
    version="0.1.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(health.router)
app.include_router(conversion.router)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint with basic API information.

    Returns:
        API information
    """
    return {
        "message": "Currency Conversion API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("currency_app.main:app", host="0.0.0.0", port=8000, reload=True)
