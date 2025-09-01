"""Main FastAPI application for load tester API."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from load_tester.routers import control


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup: Initialize load test state
    yield
    # Shutdown: Ensure any running load tests are stopped


# Create FastAPI application
app = FastAPI(
    title="Currency API Load Tester",
    description="Load testing service for currency conversion API",
    version="0.1.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(control.router)


@app.get("/")
async def root() -> dict[str, str | dict[str, str]]:
    """Root endpoint for load tester API.

    Returns:
        API information
    """
    return {
        "message": "Currency API Load Tester",
        "version": "0.1.0",
        "docs": "/docs",
        "endpoints": {
            "start": "/api/load-test/start",
            "stop": "/api/load-test/stop",
            "status": "/api/load-test/status",
        },
    }


if __name__ == "__main__":
    import uvicorn

    from load_tester.config import settings

    uvicorn.run(
        "load_tester.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
