"""Load test control endpoints."""

from fastapi import APIRouter, HTTPException, Response

from load_tester.models.load_test import LoadTestResponse, StartLoadTestRequest
from load_tester.models.reports import (
    LoadTestReport,
    format_report_as_markdown,
    generate_load_test_report,
)
from load_tester.models.scenarios import (
    LoadTestScenario,
    ScenarioConfig,
    get_scenario_config,
    list_available_scenarios,
)
from load_tester.services.load_test_manager import LoadTestManager

router = APIRouter(prefix="/api/load-test", tags=["load-test"])


@router.post("/start")
async def start_load_test(request: StartLoadTestRequest) -> LoadTestResponse:
    """Start a load test with the specified configuration.

    If a load test is already running, this will attempt to ramp to the new configuration
    instead of failing, providing seamless load transitions.

    Args:
        request: Load test start request with configuration

    Returns:
        Load test response with status and configuration

    Raises:
        HTTPException: If starting or ramping fails
    """
    manager = LoadTestManager()
    try:
        # First try to start normally
        return await manager.start_load_test(request.config)
    except RuntimeError as e:
        if "already running" in str(e).lower():
            # If test is already running, try ramping instead
            try:
                return await manager.ramp_to_config(request.config)
            except RuntimeError as ramp_error:
                raise HTTPException(status_code=409, detail=str(ramp_error)) from ramp_error
        else:
            # Other runtime errors should still fail
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
