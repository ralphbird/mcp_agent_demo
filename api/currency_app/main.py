"""Main FastAPI application for currency conversion API."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Response

from currency_app.database import create_tables
from currency_app.middleware.metrics import PrometheusMiddleware, get_metrics
from currency_app.routers import conversion, health, home, rates


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

# Add Prometheus metrics middleware
app.add_middleware(PrometheusMiddleware)

# Include routers
app.include_router(home.router)
app.include_router(health.router)
app.include_router(conversion.router)
app.include_router(rates.router)


@app.get("/api")
async def api_info() -> dict[str, str | dict[str, str]]:
    """API information endpoint.

    Returns:
        API information and available endpoints
    """
    return {
        "message": "Currency Conversion API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "convert": "/api/v1/convert",
            "rates": "/api/v1/rates",
            "rates_history": "/api/v1/rates/history",
            "metrics": "/metrics",
        },
    }


@app.get("/metrics")
async def metrics() -> Response:
    """Prometheus metrics endpoint.

    Returns:
        Prometheus metrics in text format
    """
    return Response(content=get_metrics(), media_type="text/plain")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("currency_app.main:app", host="0.0.0.0", port=8000, reload=True)
