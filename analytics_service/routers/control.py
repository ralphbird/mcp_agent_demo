"""Load test control endpoints."""

from fastapi import APIRouter, HTTPException, Response

from analytics_service.models.load_test import (
    LoadTestConfig,
    LoadTestResponse,
    StartLoadTestRequest,
)
from analytics_service.models.reports import (
    LoadTestReport,
    format_report_as_markdown,
    generate_load_test_report,
)
from analytics_service.models.scenarios import (
    LoadTestScenario,
    ScenarioConfig,
    get_scenario_config,
    list_available_scenarios,
)
from analytics_service.services.concurrent_load_test_manager import ConcurrentLoadTestManager
from analytics_service.services.load_test_manager import LoadTestManager

router = APIRouter(prefix="/api/load-test", tags=["load-test"])


@router.post("/start")
async def start_load_test(request: StartLoadTestRequest) -> LoadTestResponse:
    """Start a load test with the specified configuration.

    If a load test is already running, this will attempt to ramp to the new configuration
    instead of failing, providing seamless load transitions.

    If currency_pairs or amounts are not specified in the config, they will be
    automatically populated with all available pairs and appropriate amounts.

    Args:
        request: Load test start request with configuration

    Returns:
        Load test response with status and configuration

    Raises:
        HTTPException: If starting or ramping fails
    """
    manager = LoadTestManager()

    # Ensure the config has all currency pairs and amounts if not specified
    complete_config = request.config.ensure_complete_config()

    try:
        # First try to start normally
        return await manager.start_load_test(complete_config)
    except RuntimeError as e:
        if "already running" in str(e).lower():
            # If test is already running, try ramping instead
            try:
                return await manager.ramp_to_config(complete_config)
            except RuntimeError as ramp_error:
                raise HTTPException(status_code=409, detail=str(ramp_error)) from ramp_error
        else:
            # Other runtime errors should still fail
            raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/start/simple")
async def start_simple_load_test(
    requests_per_second: float,
    error_injection_enabled: bool = False,
    error_injection_rate: float = 0.05,
) -> LoadTestResponse:
    """Start a load test with just RPS - automatically uses all currency pairs and amounts.

    This is a simplified endpoint that automatically configures the load test to use
    all available currency pairs with amounts appropriate to each pair's from currency.

    Args:
        requests_per_second: Target requests per second (0.1 to 100.0)
        error_injection_enabled: Enable error injection for realistic testing
        error_injection_rate: Percentage of requests that should fail (0.0-0.5)

    Returns:
        Load test response with status and configuration

    Raises:
        HTTPException: If starting fails or RPS is out of range
    """
    if not (0.1 <= requests_per_second <= 2000.0):
        raise HTTPException(
            status_code=422, detail="requests_per_second must be between 0.1 and 2000.0"
        )

    if error_injection_enabled and not (0.0 <= error_injection_rate <= 0.5):
        raise HTTPException(
            status_code=422, detail="error_injection_rate must be between 0.0 and 0.5"
        )

    # Create a full configuration with all pairs and appropriate amounts
    config = LoadTestConfig.create_full_config(
        requests_per_second=requests_per_second,
        error_injection_enabled=error_injection_enabled,
        error_injection_rate=error_injection_rate,
    )

    manager = LoadTestManager()
    try:
        return await manager.start_load_test(config)
    except RuntimeError as e:
        if "already running" in str(e).lower():
            # If test is already running, try ramping instead
            try:
                return await manager.ramp_to_config(config)
            except RuntimeError as ramp_error:
                raise HTTPException(status_code=409, detail=str(ramp_error)) from ramp_error
        else:
            raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/ramp")
async def ramp_load_test(request: StartLoadTestRequest) -> LoadTestResponse:
    """Ramp the currently running load test to a new configuration.

    Args:
        request: Load test request with new configuration to ramp to

    Returns:
        Load test response with updated status and configuration

    Raises:
        HTTPException: If no load test is running or ramping fails
    """
    manager = LoadTestManager()
    try:
        return await manager.ramp_to_config(request.config)
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@router.post("/scenarios/{scenario}/ramp")
async def ramp_to_scenario(scenario: LoadTestScenario) -> LoadTestResponse:
    """Ramp the currently running load test to a scenario configuration.

    Args:
        scenario: The load test scenario to ramp to

    Returns:
        Load test response with updated status and configuration

    Raises:
        HTTPException: If scenario not found, no test running, or ramping fails
    """
    try:
        scenario_config = get_scenario_config(scenario)
        manager = LoadTestManager()
        return await manager.ramp_to_config(scenario_config.config)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario}' not found") from e
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


@router.get("/scenarios")
async def list_scenarios() -> dict[str, str]:
    """List all available load test scenarios.

    Returns:
        Dictionary mapping scenario names to descriptions
    """
    return list_available_scenarios()


@router.get("/scenarios/{scenario}")
async def get_scenario(scenario: LoadTestScenario) -> ScenarioConfig:
    """Get configuration for a specific load test scenario.

    Args:
        scenario: The load test scenario

    Returns:
        Scenario configuration

    Raises:
        HTTPException: If scenario is not found
    """
    try:
        return get_scenario_config(scenario)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario}' not found") from e


@router.post("/scenarios/{scenario}/start")
async def start_scenario_load_test(scenario: LoadTestScenario) -> LoadTestResponse:
    """Start a load test using a predefined scenario.

    If a load test is already running, this will attempt to ramp to the scenario's
    configuration instead of failing, providing seamless load transitions.

    Args:
        scenario: The load test scenario to run

    Returns:
        Load test response with status and configuration

    Raises:
        HTTPException: If scenario not found or starting/ramping fails
    """
    try:
        scenario_config = get_scenario_config(scenario)
        manager = LoadTestManager()

        # First try to start normally
        try:
            return await manager.start_load_test(scenario_config.config)
        except RuntimeError as e:
            if "already running" in str(e).lower():
                # If test is already running, try ramping instead
                return await manager.ramp_to_config(scenario_config.config)
            raise

    except KeyError as e:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario}' not found") from e
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@router.get("/report")
async def get_load_test_report() -> LoadTestReport:
    """Generate a comprehensive report of the current/last load test.

    Returns:
        Detailed load test report with analysis and recommendations
    """
    manager = LoadTestManager()
    response = await manager.get_status()
    return generate_load_test_report(response)


@router.get("/report/markdown")
async def get_load_test_report_markdown() -> Response:
    """Get load test report in Markdown format.

    Returns:
        Markdown formatted load test report
    """
    manager = LoadTestManager()
    response = await manager.get_status()
    report = generate_load_test_report(response)
    markdown_content = format_report_as_markdown(report)

    return Response(
        content=markdown_content,
        media_type="text/markdown",
        headers={"Content-Disposition": "attachment; filename=load_test_report.md"},
    )


@router.get("/scenarios/{scenario}/report")
async def get_scenario_report(scenario: LoadTestScenario) -> LoadTestReport:
    """Generate a report for a specific scenario after completion.

    Args:
        scenario: The load test scenario

    Returns:
        Detailed load test report with scenario context

    Raises:
        HTTPException: If scenario is not found
    """
    try:
        scenario_config = get_scenario_config(scenario)
        manager = LoadTestManager()
        response = await manager.get_status()
        return generate_load_test_report(response, scenario_name=scenario_config.name)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario}' not found") from e


# Global concurrent load test manager instance
concurrent_manager = ConcurrentLoadTestManager()


@router.post("/concurrent/{test_id}/start")
async def start_concurrent_load_test(
    test_id: str, request: StartLoadTestRequest
) -> LoadTestResponse:
    """Start a concurrent load test with a unique identifier.

    This allows multiple load tests to run simultaneously, useful for simulating
    baseline traffic alongside attack traffic.

    Args:
        test_id: Unique identifier for this load test instance
        request: Load test start request with configuration

    Returns:
        Load test response with status and configuration

    Raises:
        HTTPException: If test_id already exists and is running, or if starting fails
    """
    # Ensure the config has all currency pairs and amounts if not specified
    complete_config = request.config.ensure_complete_config()

    try:
        return await concurrent_manager.start_load_test(test_id, complete_config)
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@router.post("/concurrent/{test_id}/stop")
async def stop_concurrent_load_test(test_id: str) -> LoadTestResponse:
    """Stop a specific concurrent load test.

    Args:
        test_id: Identifier of the load test to stop

    Returns:
        Load test response with final status

    Raises:
        HTTPException: If test_id not found
    """
    try:
        return await concurrent_manager.stop_load_test(test_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/concurrent/stop-all")
async def stop_all_concurrent_load_tests() -> dict[str, LoadTestResponse]:
    """Stop all running concurrent load tests.

    Returns:
        Dictionary of test_id -> final response for all tests
    """
    return await concurrent_manager.stop_all_load_tests()


@router.get("/concurrent/{test_id}/status")
async def get_concurrent_load_test_status(test_id: str) -> LoadTestResponse:
    """Get status of a specific concurrent load test.

    Args:
        test_id: Identifier of the load test

    Returns:
        Load test response with current status

    Raises:
        HTTPException: If test_id not found
    """
    try:
        return await concurrent_manager.get_load_test_status(test_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/concurrent/status")
async def get_all_concurrent_load_tests_status() -> dict[str, LoadTestResponse]:
    """Get status of all concurrent load tests.

    Returns:
        Dictionary of test_id -> response for all tests
    """
    return await concurrent_manager.get_all_load_tests_status()


@router.get("/concurrent/active")
async def get_active_concurrent_test_ids() -> list[str]:
    """Get list of currently active (running or starting) concurrent test IDs.

    Returns:
        List of active test IDs
    """
    return concurrent_manager.get_active_test_ids()


@router.delete("/concurrent/cleanup")
async def cleanup_stopped_concurrent_tests() -> dict[str, str]:
    """Clean up stopped concurrent test instances to free memory.

    Returns:
        Status message
    """
    await concurrent_manager.cleanup_stopped_tests()
    return {"status": "Cleanup completed"}
