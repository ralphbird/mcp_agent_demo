"""Load test control endpoints."""

from fastapi import APIRouter, HTTPException

from load_tester.models.load_test import LoadTestResponse, StartLoadTestRequest
from load_tester.services.load_test_manager import LoadTestManager

router = APIRouter(prefix="/api/load-test", tags=["load-test"])


@router.post("/start")
async def start_load_test(request: StartLoadTestRequest) -> LoadTestResponse:
    """Start a load test with the specified configuration.

    Args:
        request: Load test start request with configuration

    Returns:
        Load test response with status and configuration

    Raises:
        HTTPException: If load test is already running
    """
    manager = LoadTestManager()
    try:
        return await manager.start_load_test(request.config)
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@router.post("/stop")
async def stop_load_test() -> LoadTestResponse:
    """Stop the currently running load test.

    Returns:
        Load test response with final status and statistics
    """
    manager = LoadTestManager()
    return await manager.stop_load_test()


@router.get("/status")
async def get_load_test_status() -> LoadTestResponse:
    """Get the current status and statistics of the load test.

    Returns:
        Current load test status and statistics
    """
    manager = LoadTestManager()
    return await manager.get_status()
