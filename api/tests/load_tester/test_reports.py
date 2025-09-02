"""Tests for load test reporting functionality."""

from datetime import UTC, datetime

import pytest
from load_tester.models.load_test import (
    LoadTestConfig,
    LoadTestResponse,
    LoadTestStats,
    LoadTestStatus,
)
from load_tester.models.reports import (
    LoadTestReport,
    ReportFormat,
    format_report_as_markdown,
    generate_load_test_report,
)


class TestLoadTestReports:
    """Test load test reporting functionality."""

    @pytest.fixture
    def sample_response(self):
        """Create a sample load test response for testing."""
        config = LoadTestConfig(
            requests_per_second=5.0, currency_pairs=["USD_EUR", "USD_GBP"], amounts=[100.0, 500.0]
        )

        stats = LoadTestStats(
            total_requests=100,
            successful_requests=95,
            failed_requests=5,
            avg_response_time_ms=150.5,
            min_response_time_ms=85.2,
            max_response_time_ms=280.1,
            requests_per_second=4.8,
        )

        started_at = datetime(2023, 10, 1, 10, 0, 0, tzinfo=UTC)
        stopped_at = datetime(2023, 10, 1, 10, 2, 0, tzinfo=UTC)

        return LoadTestResponse(
            status=LoadTestStatus.STOPPED,
            config=config,
            stats=stats,
            started_at=started_at,
            stopped_at=stopped_at,
        )

    def test_report_format_enum(self):
        """Test ReportFormat enum values."""
        assert ReportFormat.JSON == "json"
        assert ReportFormat.MARKDOWN == "markdown"
        assert ReportFormat.HTML == "html"
        assert ReportFormat.TEXT == "text"

    def test_generate_load_test_report_basic(self, sample_response):
        """Test generating a basic load test report."""
        report = generate_load_test_report(sample_response)

        assert isinstance(report, LoadTestReport)
        assert report.status == LoadTestStatus.STOPPED
        assert report.requests_per_second == 5.0
        assert report.currency_pairs == ["USD_EUR", "USD_GBP"]
        assert report.amounts == [100.0, 500.0]
        assert report.duration_seconds == 120.0  # 2 minutes
        assert report.success_rate == 95.0  # 95/100
        assert report.avg_rps_achieved == pytest.approx(
            0.833, rel=1e-2
        )  # 100 requests / 120 seconds

    def test_generate_load_test_report_with_scenario(self, sample_response):
        """Test generating report with scenario name."""
        report = generate_load_test_report(
            sample_response, scenario_name="Light Load Test", test_id="test_123"
        )

        assert report.scenario_name == "Light Load Test"
        assert report.test_id == "test_123"

    def test_generate_load_test_report_performance_grading(self, sample_response):
        """Test performance grading calculation."""
        report = generate_load_test_report(sample_response)

        # With 95% success rate, 150ms avg response time, but low throughput
        # (0.83 achieved vs 5.0 target RPS), grade might be lower
        assert report.performance_grade in ["A", "B", "C", "D"]
        assert len(report.recommendations) > 0

    def test_generate_load_test_report_no_timing(self):
        """Test report generation without timing information."""
        response = LoadTestResponse(status=LoadTestStatus.IDLE, stats=LoadTestStats())

        report = generate_load_test_report(response)
        assert report.duration_seconds is None
        assert report.started_at is None
        assert report.stopped_at is None
        assert report.success_rate == 0.0
        assert report.avg_rps_achieved == 0.0

    def test_performance_grade_calculation_excellent(self):
        """Test performance grade calculation for excellent performance."""
        from load_tester.models.reports import _calculate_performance_grade

        # Excellent performance: 100% success, 50ms response time, meeting target RPS
        grade = _calculate_performance_grade(
            success_rate=100.0, avg_response_time=50.0, achieved_rps=5.0, target_rps=5.0
        )
        assert grade == "A"

    def test_performance_grade_calculation_poor(self):
        """Test performance grade calculation for poor performance."""
        from load_tester.models.reports import _calculate_performance_grade

        # Poor performance: 60% success, 3000ms response time, low throughput
        grade = _calculate_performance_grade(
            success_rate=60.0, avg_response_time=3000.0, achieved_rps=1.0, target_rps=5.0
        )
        assert grade == "F"

    def test_performance_grade_calculation_no_target(self):
        """Test performance grade calculation without target RPS."""
        from load_tester.models.reports import _calculate_performance_grade

        grade = _calculate_performance_grade(
            success_rate=95.0,
            avg_response_time=200.0,
            achieved_rps=3.0,
            target_rps=0,  # No target
        )
        # Should still get reasonable grade without target comparison
        assert grade in ["A", "B", "C"]

    def test_generate_recommendations_excellent_performance(self):
        """Test recommendations for excellent performance."""
        from load_tester.models.reports import _generate_recommendations

        recommendations = _generate_recommendations(
            success_rate=99.5, avg_response_time=120.0, achieved_rps=5.0, target_rps=5.0
        )

        assert len(recommendations) > 0
        assert any("excellent" in rec.lower() for rec in recommendations)

    def test_generate_recommendations_poor_performance(self):
        """Test recommendations for poor performance."""
        from load_tester.models.reports import _generate_recommendations

        recommendations = _generate_recommendations(
            success_rate=75.0, avg_response_time=2000.0, achieved_rps=2.0, target_rps=5.0
        )

        assert len(recommendations) > 0
        assert any("success rate" in rec.lower() for rec in recommendations)
        assert any("response time" in rec.lower() for rec in recommendations)
        assert any("throughput" in rec.lower() for rec in recommendations)

    def test_format_report_as_markdown(self, sample_response):
        """Test formatting report as Markdown."""
        report = generate_load_test_report(sample_response)
        markdown = format_report_as_markdown(report)

        assert isinstance(markdown, str)
        assert "# Load Test Report" in markdown
        assert "## Test Summary" in markdown
        assert "## Performance Metrics" in markdown
        assert "## Recommendations" in markdown
        assert f"**Performance Grade**: **{report.performance_grade}**" in markdown
        assert "95.0%" in markdown  # Success rate
        assert "150.5ms" in markdown  # Avg response time

    def test_format_report_markdown_with_error(self):
        """Test formatting report with error message."""
        response = LoadTestResponse(
            status=LoadTestStatus.ERROR, stats=LoadTestStats(), error_message="Connection timeout"
        )

        report = generate_load_test_report(response)
        markdown = format_report_as_markdown(report)

        assert "## Error Details" in markdown
        assert "Connection timeout" in markdown

    def test_report_currency_formatting(self, sample_response):
        """Test currency amount formatting in reports."""
        report = generate_load_test_report(sample_response)
        markdown = format_report_as_markdown(report)

        # Should format amounts as currency
        assert "$100" in markdown
        assert "$500" in markdown

    def test_report_recommendation_numbering(self, sample_response):
        """Test that recommendations are properly numbered."""
        report = generate_load_test_report(sample_response)
        markdown = format_report_as_markdown(report)

        # Should have numbered recommendations
        recommendation_lines = [
            line for line in markdown.split("\n") if line.strip().startswith(("1.", "2.", "3."))
        ]
        assert len(recommendation_lines) >= 1
