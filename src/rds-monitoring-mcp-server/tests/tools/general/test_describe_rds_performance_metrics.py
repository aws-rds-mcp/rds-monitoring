"""Tests for the describe_rds_performance_metrics module."""

import json
import pytest
from awslabs.rds_monitoring_mcp_server.tools.general.describe_rds_performance_metrics import (
    CLUSTER_METRICS,
    GLOBAL_CLUSTER_METRICS,
    INSTANCE_METRICS,
    DetailedMetricItem,
    build_metric_queries,
    describe_rds_performance_metrics,
    get_metric_statistics,
    process_metric_data,
)
from datetime import datetime, timezone
from unittest.mock import MagicMock


def create_test_datapoint():
    """Create a sample CloudWatch datapoint for testing."""
    return {
        'Timestamp': datetime(2025, 1, 1, tzinfo=timezone.utc),
        'Average': 42.0,
        'Minimum': 10.0,
        'Maximum': 90.0,
        'SampleCount': 5.0,
        'Sum': 210.0,
        'Unit': 'Count',
    }


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
        'Messages': [{'Code': 'Info', 'Value': 'Test message'}],
    }


class TestHelperFunctions:
    """Tests for helper functions in describe_rds_performance_metrics."""

    @pytest.mark.asyncio
    async def test_get_metric_statistics(self, mock_cloudwatch_client):
        """Test the get_metric_statistics function."""
        mock_cloudwatch_client.get_metric_statistics.return_value = {
            'Label': 'CPUUtilization',
            'Datapoints': [create_test_datapoint()],
        }

        result = await get_metric_statistics(
            metric_name='CPUUtilization',
            start_time='2025-01-01T00:00:00Z',
            end_time='2025-01-02T00:00:00Z',
            period=60,
        )

        mock_cloudwatch_client.get_metric_statistics.assert_called_once()
        call_kwargs = mock_cloudwatch_client.get_metric_statistics.call_args[1]
        assert call_kwargs['MetricName'] == 'CPUUtilization'
        assert call_kwargs['Period'] == 60

        assert result['Label'] == 'CPUUtilization'
        assert len(result['Datapoints']) == 1

        await get_metric_statistics(
            metric_name='CPUUtilization',
            start_time='2025-01-01T00:00:00Z',
            end_time='2025-01-02T00:00:00Z',
            period=60,
            dimensions=[{'DBInstanceIdentifier': 'test-instance'}],
        )

        call_kwargs = mock_cloudwatch_client.get_metric_statistics.call_args[1]
        assert len(call_kwargs['Dimensions']) == 1
        assert call_kwargs['Dimensions'][0]['Name'] == 'DBInstanceIdentifier'
        assert call_kwargs['Dimensions'][0]['Value'] == 'test-instance'

        await get_metric_statistics(
            metric_name='CPUUtilization',
            start_time='2025-01-01T00:00:00Z',
            end_time='2025-01-02T00:00:00Z',
            period=60,
            dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': 'test-instance'}],
        )

        call_kwargs = mock_cloudwatch_client.get_metric_statistics.call_args[1]
        assert len(call_kwargs['Dimensions']) == 1
        assert call_kwargs['Dimensions'][0]['Name'] == 'DBInstanceIdentifier'
        assert call_kwargs['Dimensions'][0]['Value'] == 'test-instance'

        await get_metric_statistics(
            metric_name='CPUUtilization',
            start_time='2025-01-01T00:00:00Z',
            end_time='2025-01-02T00:00:00Z',
            period=60,
            statistics=['Average', 'Maximum'],
            unit='Percent',
        )

        call_kwargs = mock_cloudwatch_client.get_metric_statistics.call_args[1]
        assert call_kwargs['Statistics'] == ['Average', 'Maximum']
        assert call_kwargs['Unit'] == 'Percent'

    def test_build_metric_queries(self):
        """Test the build_metric_queries function."""
        instance_queries = build_metric_queries(
            resource_type='instance',
            resource_identifier='test-instance',
            period=60,
            stat='Average',
        )

        assert len(instance_queries) == len(INSTANCE_METRICS)
        for query, metric in zip(instance_queries, INSTANCE_METRICS):
            assert query['Id'] == f'metric_{metric}_Average'
            assert query['MetricStat']['Metric']['MetricName'] == metric
            assert query['MetricStat']['Metric']['Dimensions'][0]['Name'] == 'DBInstanceIdentifier'
            assert query['MetricStat']['Metric']['Dimensions'][0]['Value'] == 'test-instance'
            assert query['MetricStat']['Period'] == 60
            assert query['MetricStat']['Stat'] == 'Average'

        cluster_queries = build_metric_queries(
            resource_type='cluster',
            resource_identifier='test-cluster',
            period=300,
            stat='Maximum',
        )

        assert len(cluster_queries) == len(CLUSTER_METRICS)
        for query, metric in zip(cluster_queries, CLUSTER_METRICS):
            assert query['Id'] == f'metric_{metric}_Maximum'
            assert query['MetricStat']['Metric']['MetricName'] == metric
            assert query['MetricStat']['Metric']['Dimensions'][0]['Name'] == 'DBClusterIdentifier'
            assert query['MetricStat']['Metric']['Dimensions'][0]['Value'] == 'test-cluster'
            assert query['MetricStat']['Period'] == 300
            assert query['MetricStat']['Stat'] == 'Maximum'

        global_cluster_queries = build_metric_queries(
            resource_type='global_cluster',
            resource_identifier='test-global-cluster',
            period=3600,
            stat='Sum',
        )

        assert len(global_cluster_queries) == len(GLOBAL_CLUSTER_METRICS)
        for query, metric in zip(global_cluster_queries, GLOBAL_CLUSTER_METRICS):
            assert query['Id'] == f'metric_{metric}_Sum'
            assert query['MetricStat']['Metric']['MetricName'] == metric
            assert query['MetricStat']['Metric']['Dimensions'][0]['Name'] == 'DBClusterIdentifier'
            assert query['MetricStat']['Metric']['Dimensions'][0]['Value'] == 'test-global-cluster'
            assert query['MetricStat']['Period'] == 3600
            assert query['MetricStat']['Stat'] == 'Sum'

    def test_process_metric_data(self):
        """Test the process_metric_data function."""
        metric_data = create_test_metric_data_result()
        result = process_metric_data(metric_data)

        assert isinstance(result, DetailedMetricItem)
        assert result.id == 'metric_CPUUtilization_Average'
        assert result.label == 'CPUUtilization_Average'
        assert len(result.timestamps) == 2
        assert len(result.values) == 2
        assert result.status_code == 'Complete'
        assert len(result.messages) == 1
        assert result.messages[0].code == 'Info'
        assert result.messages[0].value == 'Test message'

        metric_data_no_messages = {
            'Id': 'metric_CPUUtilization_Average',
            'Label': 'CPUUtilization_Average',
            'Timestamps': [
                datetime(2025, 1, 1, tzinfo=timezone.utc),
                datetime(2025, 1, 1, 1, tzinfo=timezone.utc),
            ],
            'Values': [42.0, 45.0],
            'StatusCode': 'Complete',
        }

        result_no_messages = process_metric_data(metric_data_no_messages)
        assert result_no_messages.messages is None

        metric_data_empty_messages = {
            'Id': 'metric_CPUUtilization_Average',
            'Label': 'CPUUtilization_Average',
            'Timestamps': [
                datetime(2025, 1, 1, tzinfo=timezone.utc),
                datetime(2025, 1, 1, 1, tzinfo=timezone.utc),
            ],
            'Values': [42.0, 45.0],
            'StatusCode': 'Complete',
            'Messages': [],
        }

        result_empty_messages = process_metric_data(metric_data_empty_messages)
        assert result_empty_messages.messages is None


class TestDescribeRDSPerformanceMetrics:
    """Tests for the describe_rds_performance_metrics function."""

    @pytest.mark.asyncio
    async def test_describe_rds_performance_metrics_instance(self, mock_cloudwatch_client):
        """Test the describe_rds_performance_metrics function for instances."""
        paginator_mock = MagicMock()
        mock_cloudwatch_client.get_paginator.return_value = paginator_mock

        paginator_mock.paginate.return_value = [
            {
                'MetricDataResults': [create_test_metric_data_result()],
            }
        ]

        result = await describe_rds_performance_metrics(
            resource_identifier='test-instance',
            resource_type='instance',
            start_date='2025-01-01T00:00:00Z',
            end_date='2025-01-02T00:00:00Z',
            period=60,
            stat='Average',
            scan_by='TimestampDescending',
        )

        mock_cloudwatch_client.get_paginator.assert_called_once_with('get_metric_data')
        paginator_mock.paginate.assert_called_once()

        paginate_kwargs = paginator_mock.paginate.call_args[1]
        assert len(paginate_kwargs['MetricDataQueries']) == len(INSTANCE_METRICS)
        assert paginate_kwargs['ScanBy'] == 'TimestampDescending'

        result_dict = json.loads(result)
        assert isinstance(result_dict, dict)

    @pytest.mark.asyncio
    async def test_describe_rds_performance_metrics_cluster(self, mock_cloudwatch_client):
        """Test the describe_rds_performance_metrics function for clusters."""
        paginator_mock = MagicMock()
        mock_cloudwatch_client.get_paginator.return_value = paginator_mock

        paginator_mock.paginate.return_value = [
            {
                'MetricDataResults': [create_test_metric_data_result()],
            }
        ]

        await describe_rds_performance_metrics(
            resource_identifier='test-cluster',
            resource_type='cluster',
            start_date='2025-01-01T00:00:00Z',
            end_date='2025-01-02T00:00:00Z',
            period=300,
            stat='Maximum',
            scan_by='TimestampAscending',
        )

        paginate_kwargs = paginator_mock.paginate.call_args[1]
        assert len(paginate_kwargs['MetricDataQueries']) == len(CLUSTER_METRICS)
        assert paginate_kwargs['ScanBy'] == 'TimestampAscending'

        first_query = paginate_kwargs['MetricDataQueries'][0]
        assert (
            first_query['MetricStat']['Metric']['Dimensions'][0]['Name'] == 'DBClusterIdentifier'
        )
        assert first_query['MetricStat']['Metric']['Dimensions'][0]['Value'] == 'test-cluster'

    @pytest.mark.asyncio
    async def test_describe_rds_performance_metrics_global_cluster(self, mock_cloudwatch_client):
        """Test the describe_rds_performance_metrics function for global clusters."""
        paginator_mock = MagicMock()
        mock_cloudwatch_client.get_paginator.return_value = paginator_mock

        paginator_mock.paginate.return_value = [
            {
                'MetricDataResults': [create_test_metric_data_result()],
            }
        ]

        await describe_rds_performance_metrics(
            resource_identifier='test-global-cluster',
            resource_type='global_cluster',
            start_date='2025-01-01T00:00:00Z',
            end_date='2025-01-02T00:00:00Z',
            period=3600,
            stat='Sum',
            scan_by='TimestampDescending',
        )

        paginate_kwargs = paginator_mock.paginate.call_args[1]
        assert len(paginate_kwargs['MetricDataQueries']) == len(GLOBAL_CLUSTER_METRICS)

        first_query = paginate_kwargs['MetricDataQueries'][0]
        assert (
            first_query['MetricStat']['Metric']['Dimensions'][0]['Name'] == 'DBClusterIdentifier'
        )
        assert (
            first_query['MetricStat']['Metric']['Dimensions'][0]['Value'] == 'test-global-cluster'
        )

    @pytest.mark.asyncio
    async def test_describe_rds_performance_metrics_pagination(self, mock_cloudwatch_client):
        """Test the describe_rds_performance_metrics function with pagination."""
        paginator_mock = MagicMock()
        mock_cloudwatch_client.get_paginator.return_value = paginator_mock

        result1 = create_test_metric_data_result()
        result1['Id'] = 'metric_CPUUtilization_Average'

        result2 = create_test_metric_data_result()
        result2['Id'] = 'metric_FreeableMemory_Average'

        paginator_mock.paginate.return_value = [
            {'MetricDataResults': [result1]},
            {'MetricDataResults': [result2]},
        ]

        result = await describe_rds_performance_metrics(
            resource_identifier='test-instance',
            resource_type='instance',
            start_date='2025-01-01T00:00:00Z',
            end_date='2025-01-02T00:00:00Z',
            period=60,
            stat='Average',
            scan_by='TimestampDescending',
        )

        result_dict = json.loads(result)
        assert isinstance(result_dict, dict)

    @pytest.mark.asyncio
    async def test_describe_rds_performance_metrics_empty_results(self, mock_cloudwatch_client):
        """Test the describe_rds_performance_metrics function with empty results."""
        paginator_mock = MagicMock()
        mock_cloudwatch_client.get_paginator.return_value = paginator_mock

        paginator_mock.paginate.return_value = [
            {'MetricDataResults': []},
        ]

        result = await describe_rds_performance_metrics(
            resource_identifier='test-instance',
            resource_type='instance',
            start_date='2025-01-01T00:00:00Z',
            end_date='2025-01-02T00:00:00Z',
            period=60,
            stat='Average',
            scan_by='TimestampDescending',
        )

        result_dict = json.loads(result)
        assert isinstance(result_dict, dict)
