"""Main FastAPI application for load tester API."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Response

from load_tester.logging_config import configure_logging, get_logger
from load_tester.middleware.logging import LoggingMiddleware
from load_tester.middleware.metrics import LoadTesterPrometheusMiddleware, get_load_tester_metrics
from load_tester.routers import control

# Configure logging at module level
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup: Initialize load test state
    logger.info("Starting Load Tester application")
    logger.info("Load Tester application started successfully")
    yield

    # Shutdown: Ensure any running load tests are stopped
    logger.info("Shutting down Load Tester application")


# Create FastAPI application
app = FastAPI(
    title="Currency API Load Tester",
    description="Load testing service for currency conversion API",
    version="0.1.0",
    lifespan=lifespan,
)

# Add middleware (order matters - logging should be first to capture all requests)
app.add_middleware(LoggingMiddleware)
app.add_middleware(LoadTesterPrometheusMiddleware)

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
            "report": "/api/load-test/report",
            "report_markdown": "/api/load-test/report/markdown",
            "scenarios": "/api/load-test/scenarios",
            "scenario_start": "/api/load-test/scenarios/{scenario}/start",
            "scenario_report": "/api/load-test/scenarios/{scenario}/report",
            "metrics": "/metrics",
        },
    }


@app.get("/metrics")
async def metrics() -> Response:
    """Prometheus metrics endpoint.

    Returns:
        Prometheus metrics in text format
    """
    return Response(content=get_load_tester_metrics(), media_type="text/plain")


if __name__ == "__main__":
    import uvicorn

    from load_tester.config import settings

    uvicorn.run(
        "load_tester.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
