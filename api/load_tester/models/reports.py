"""Load test reporting models and utilities."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from load_tester.models.load_test import LoadTestResponse, LoadTestStats, LoadTestStatus


class ReportFormat(str, Enum):
    """Available report formats."""

    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"
    TEXT = "text"


class LoadTestReport(BaseModel):
    """Comprehensive load test execution report."""

    test_id: str = Field(description="Unique identifier for this test run")
    scenario_name: str | None = Field(description="Scenario name if applicable")
    status: LoadTestStatus = Field(description="Final test status")

    # Test configuration
    requests_per_second: float = Field(description="Configured requests per second")
    currency_pairs: list[str] = Field(description="Currency pairs tested")
    amounts: list[float] = Field(description="Transaction amounts tested")

    # Execution timing
    started_at: datetime | None = Field(description="Test start time")
    stopped_at: datetime | None = Field(description="Test end time")
    duration_seconds: float | None = Field(description="Total test duration")

    # Performance metrics
    stats: LoadTestStats = Field(description="Detailed performance statistics")

    # Analysis results
    success_rate: float = Field(description="Success rate as percentage")
    avg_rps_achieved: float = Field(description="Average requests per second achieved")
    performance_grade: str = Field(description="Overall performance assessment")

    # Recommendations
    recommendations: list[str] = Field(description="Performance recommendations")
    error_message: str | None = Field(description="Error message if test failed")


def generate_load_test_report(
    response: LoadTestResponse, scenario_name: str | None = None, test_id: str | None = None
) -> LoadTestReport:
    """Generate a comprehensive load test report from response data.

    Args:
        response: Load test response data
        scenario_name: Optional scenario name
        test_id: Optional test identifier

    Returns:
        Comprehensive load test report
    """
    # Calculate derived metrics
    duration = None
    if response.started_at and response.stopped_at:
        duration = (response.stopped_at - response.started_at).total_seconds()

    success_rate = 0.0
    if response.stats.total_requests > 0:
        success_rate = (response.stats.successful_requests / response.stats.total_requests) * 100

    # Calculate actual RPS achieved
    avg_rps_achieved = 0.0
    if duration and duration > 0:
        avg_rps_achieved = response.stats.total_requests / duration

    # Performance grading
    performance_grade = _calculate_performance_grade(
        success_rate,
        response.stats.avg_response_time_ms,
        avg_rps_achieved,
        response.config.requests_per_second if response.config else 0,
    )

    # Generate recommendations
    recommendations = _generate_recommendations(
        success_rate,
        response.stats.avg_response_time_ms,
        avg_rps_achieved,
        response.config.requests_per_second if response.config else 0,
    )

    return LoadTestReport(
        test_id=test_id or f"test_{int(datetime.now().timestamp())}",
        scenario_name=scenario_name,
        status=response.status,
        requests_per_second=response.config.requests_per_second if response.config else 0,
        currency_pairs=response.config.currency_pairs if response.config else [],
        amounts=response.config.amounts if response.config else [],
        started_at=response.started_at,
        stopped_at=response.stopped_at,
        duration_seconds=duration,
        stats=response.stats,
        success_rate=success_rate,
        avg_rps_achieved=avg_rps_achieved,
        performance_grade=performance_grade,
        recommendations=recommendations,
        error_message=response.error_message,
    )


def _calculate_performance_grade(
    success_rate: float, avg_response_time: float, achieved_rps: float, target_rps: float
) -> str:
    """Calculate overall performance grade based on metrics.

    Args:
        success_rate: Success rate percentage
        avg_response_time: Average response time in milliseconds
        achieved_rps: Actual requests per second achieved
        target_rps: Target requests per second

    Returns:
        Performance grade (A, B, C, D, F)
    """
    score = 0

    # Success rate scoring (40% of grade)
    if success_rate >= 99:
        score += 40
    elif success_rate >= 95:
        score += 35
    elif success_rate >= 90:
        score += 30
    elif success_rate >= 80:
        score += 20
    elif success_rate >= 50:
        score += 10

    # Response time scoring (35% of grade)
    if avg_response_time <= 100:
        score += 35
    elif avg_response_time <= 250:
        score += 30
    elif avg_response_time <= 500:
        score += 25
    elif avg_response_time <= 1000:
        score += 15
    elif avg_response_time <= 2000:
        score += 5

    # Throughput scoring (25% of grade)
    if target_rps > 0:
        throughput_ratio = achieved_rps / target_rps
        if throughput_ratio >= 0.95:
            score += 25
        elif throughput_ratio >= 0.85:
            score += 20
        elif throughput_ratio >= 0.75:
            score += 15
        elif throughput_ratio >= 0.50:
            score += 10
        elif throughput_ratio >= 0.25:
            score += 5
    else:
        score += 25  # No target, assume good

    # Convert score to grade
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def _generate_recommendations(
    success_rate: float, avg_response_time: float, achieved_rps: float, target_rps: float
) -> list[str]:
    """Generate performance recommendations based on test results.

    Args:
        success_rate: Success rate percentage
        avg_response_time: Average response time in milliseconds
        achieved_rps: Actual requests per second achieved
        target_rps: Target requests per second

    Returns:
        List of performance recommendations
    """
    recommendations = []

    # Success rate recommendations
    if success_rate < 95:
        if success_rate < 80:
            recommendations.append(
                "Critical: Very low success rate indicates system overload or errors"
            )
        else:
            recommendations.append("Warning: Success rate below 95% - investigate error causes")

    # Response time recommendations
    if avg_response_time > 1000:
        recommendations.append("High response times detected - consider scaling or optimization")
    elif avg_response_time > 500:
        recommendations.append("Moderate response time increase - monitor for degradation trends")

    # Throughput recommendations
    if target_rps > 0:
        throughput_ratio = achieved_rps / target_rps
        if throughput_ratio < 0.75:
            recommendations.append(
                "Throughput significantly below target - system may be bottlenecked"
            )
        elif throughput_ratio < 0.90:
            recommendations.append("Throughput slightly below target - minor performance impact")

    # Positive recommendations
    if success_rate >= 99 and avg_response_time <= 250:
        recommendations.append("Excellent performance - system handling load very well")
    elif success_rate >= 95 and avg_response_time <= 500:
        recommendations.append("Good performance - system within acceptable parameters")

    # General recommendations
    if not recommendations:
        recommendations.append("Performance appears normal - continue monitoring")

    return recommendations


def format_report_as_markdown(report: LoadTestReport) -> str:
    """Format load test report as Markdown.

    Args:
        report: Load test report

    Returns:
        Markdown formatted report
    """
    md = f"""# Load Test Report

## Test Summary
- **Test ID**: {report.test_id}
- **Scenario**: {report.scenario_name or "Custom"}
- **Status**: {report.status.value.upper()}
- **Performance Grade**: **{report.performance_grade}**

## Test Configuration
- **Target RPS**: {report.requests_per_second}
- **Currency Pairs**: {", ".join(report.currency_pairs)}
- **Test Amounts**: {", ".join(f"${amt:,.0f}" for amt in report.amounts)}

## Execution Timeline
- **Started**: {report.started_at.isoformat() if report.started_at else "N/A"}
- **Stopped**: {report.stopped_at.isoformat() if report.stopped_at else "N/A"}
- **Duration**: {report.duration_seconds:.1f}s

## Performance Metrics
- **Total Requests**: {report.stats.total_requests:,}
- **Successful**: {report.stats.successful_requests:,} ({report.success_rate:.1f}%)
- **Failed**: {report.stats.failed_requests:,}
- **Avg Response Time**: {report.stats.avg_response_time_ms:.1f}ms
- **Min Response Time**: {report.stats.min_response_time_ms:.1f}ms
- **Max Response Time**: {report.stats.max_response_time_ms:.1f}ms
- **Achieved RPS**: {report.avg_rps_achieved:.2f}

## Recommendations
"""

    for i, rec in enumerate(report.recommendations, 1):
        md += f"{i}. {rec}\n"

    if report.error_message:
        md += f"\n## Error Details\n```\n{report.error_message}\n```\n"

    return md
