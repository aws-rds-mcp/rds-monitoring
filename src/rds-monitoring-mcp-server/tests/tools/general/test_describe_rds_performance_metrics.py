"""Tests for the describe_rds_performance_metrics module."""

import pytest
from awslabs.rds_monitoring_mcp_server.tools.general.describe_rds_performance_metrics import (
    MetricSummary,
    MetricSummaryList,
    describe_rds_performance_metrics,
)
from datetime import datetime, timezone


def create_test_metric_data_result():
    """Create a sample CloudWatch metric data result for testing."""
    return {
        'Id': 'metric_CPUUtilization_Average',
        'Label': 'CPUUtilization_Average',
        'Timestamps': [
            datetime(2025, 1, 1, tzinfo=timezone.utc),
            datetime(2025, 1, 1, 1, tzinfo=timezone.utc),
        ],
        'Values': [42.0, 45.0],
        'StatusCode': 'Complete',
    }


class TestMetricSummary:
    """Tests for MetricSummary model."""

    def test_from_metric_data_with_values(self):
        """Test MetricSummary.from_metric_data with values."""
        metric_data = {
            'Id': 'metric_CPUUtilization_Average',
            'Label': 'CPUUtilization_Average',
            'Values': [40.0, 50.0, 60.0],
            'Timestamps': [
                datetime(2025, 1, 1, 2, tzinfo=timezone.utc),
                datetime(2025, 1, 1, 1, tzinfo=timezone.utc),
                datetime(2025, 1, 1, 0, tzinfo=timezone.utc),
            ],
            'StatusCode': 'Complete',
        }

        result = MetricSummary.from_metric_data(metric_data)

        assert result.id == 'metric_CPUUtilization_Average'
        assert result.label == 'CPUUtilization_Average'
        assert result.data_status == 'Complete'
        assert result.current_value == 40.0  # First value (newest timestamp)
        assert result.min_value == 40.0
        assert result.max_value == 60.0
        assert result.avg_value == 50.0
        assert result.change_percent == -33.33  # (40-60)/60*100
        assert result.trend == 'decreasing'
        assert result.data_points_count == 3

    def test_from_metric_data_empty_values(self):
        """Test MetricSummary.from_metric_data with empty values."""
        metric_data = {
            'Id': 'metric_CPUUtilization_Average',
            'Label': 'CPUUtilization_Average',
            'Values': [],
            'Timestamps': [],
            'StatusCode': 'Complete',
        }

        result = MetricSummary.from_metric_data(metric_data)

        assert result.id == 'metric_CPUUtilization_Average'
        assert result.current_value == 0
        assert result.trend == 'no_data'
        assert result.data_points_count == 0

    def test_from_metric_data_stable_trend(self):
        """Test MetricSummary trend calculation for stable values."""
        metric_data = {
            'Id': 'metric_test',
            'Label': 'test',
            'Values': [50.0, 50.5],
            'Timestamps': [
                datetime(2025, 1, 1, 1, tzinfo=timezone.utc),
                datetime(2025, 1, 1, 0, tzinfo=timezone.utc),
            ],
            'StatusCode': 'Complete',
        }

        result = MetricSummary.from_metric_data(metric_data)
        assert result.trend == 'stable'  # 1% change

    def test_from_metric_data_increasing_trend(self):
        """Test MetricSummary trend calculation for increasing values."""
        metric_data = {
            'Id': 'metric_test',
            'Label': 'test',
            'Values': [60.0, 50.0],
            'Timestamps': [
                datetime(2025, 1, 1, 1, tzinfo=timezone.utc),
                datetime(2025, 1, 1, 0, tzinfo=timezone.utc),
            ],
            'StatusCode': 'Complete',
        }

        result = MetricSummary.from_metric_data(metric_data)
        assert result.trend == 'increasing'  # 20% change


class TestDescribeRDSPerformanceMetrics:
    """Tests for the describe_rds_performance_metrics function."""

    @pytest.mark.asyncio
    async def test_describe_rds_performance_metrics_instance(
        self, mock_cloudwatch_client, mock_handle_paginated_call
    ):
        """Test the describe_rds_performance_metrics function for instances."""
        mock_summary = MetricSummary(
            id='metric_CPUUtilization_Average',
            label='CPUUtilization_Average',
            data_status='Complete',
            current_value=50.0,
            min_value=40.0,
            max_value=60.0,
            avg_value=50.0,
            trend='stable',
            change_percent=0.0,
            data_points_count=10,
        )
        mock_handle_paginated_call.return_value = [mock_summary]

        result = await describe_rds_performance_metrics(
            resource_identifier='test-instance',
            resource_type='INSTANCE',
            start_date='2025-01-01T00:00:00Z',
            end_date='2025-01-02T00:00:00Z',
            period=60,
            stat='Average',
            scan_by='TimestampDescending',
        )

        assert isinstance(result, MetricSummaryList)
        assert result.resource_identifier == 'test-instance'
        assert result.resource_type == 'INSTANCE'

    @pytest.mark.asyncio
    async def test_describe_rds_performance_metrics_cluster(
        self, mock_cloudwatch_client, mock_handle_paginated_call
    ):
        """Test the describe_rds_performance_metrics function for clusters."""
        mock_summary = MetricSummary(
            id='metric_VolumeBytesUsed_Average',
            label='VolumeBytesUsed_Average',
            data_status='Complete',
            current_value=1000.0,
            min_value=900.0,
            max_value=1100.0,
            avg_value=1000.0,
            trend='stable',
            change_percent=0.0,
            data_points_count=5,
        )
        mock_handle_paginated_call.return_value = [mock_summary]

        result = await describe_rds_performance_metrics(
            resource_identifier='test-cluster',
            resource_type='CLUSTER',
            start_date='2025-01-01T00:00:00Z',
            end_date='2025-01-02T00:00:00Z',
            period=300,
            stat='Maximum',
            scan_by='TimestampAscending',
        )

        assert result.resource_type == 'CLUSTER'

    @pytest.mark.asyncio
    async def test_describe_rds_performance_metrics_global_cluster(
        self, mock_cloudwatch_client, mock_handle_paginated_call
    ):
        """Test the describe_rds_performance_metrics function for global clusters."""
        mock_summary = MetricSummary(
            id='metric_AuroraGlobalDBReplicationLag_Average',
            label='AuroraGlobalDBReplicationLag_Average',
            data_status='Complete',
            current_value=100.0,
            min_value=50.0,
            max_value=150.0,
            avg_value=100.0,
            trend='stable',
            change_percent=0.0,
            data_points_count=8,
        )
        mock_handle_paginated_call.return_value = [mock_summary]

        result = await describe_rds_performance_metrics(
            resource_identifier='test-global-cluster',
            resource_type='GLOBAL_CLUSTER',
            start_date='2025-01-01T00:00:00Z',
            end_date='2025-01-02T00:00:00Z',
            period=3600,
            stat='Sum',
            scan_by='TimestampDescending',
        )

        assert result.resource_type == 'GLOBAL_CLUSTER'
