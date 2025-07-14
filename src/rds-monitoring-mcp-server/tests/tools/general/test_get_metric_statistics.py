# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for get_metric_statistics module."""

import pytest
from awslabs.rds_monitoring_mcp_server.tools.general.get_metric_statistics import (
    MetricDatapoint,
    MetricDimension,
    MetricStatisticsResult,
    _get_metric_statistics_core,
    format_dimensions,
)
from datetime import datetime


class TestMetricDimension:
    """Test MetricDimension model."""

    def test_metric_dimension_creation(self):
        """Test creating a MetricDimension."""
        dimension = MetricDimension(Name='DBInstanceIdentifier', Value='test-db')
        assert dimension.Name == 'DBInstanceIdentifier'
        assert dimension.Value == 'test-db'


class TestMetricDatapoint:
    """Test MetricDatapoint model."""

    def test_metric_datapoint_creation(self):
        """Test creating a MetricDatapoint."""
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        datapoint = MetricDatapoint(
            Timestamp=timestamp,
            Average=50.0,
            Sum=100.0,
            Maximum=75.0,
            Minimum=25.0,
            SampleCount=10.0,
            Unit='Percent',
        )
        assert datapoint.Timestamp == timestamp
        assert datapoint.Average == 50.0
        assert datapoint.Sum == 100.0
        assert datapoint.Maximum == 75.0
        assert datapoint.Minimum == 25.0
        assert datapoint.SampleCount == 10.0
        assert datapoint.Unit == 'Percent'

    def test_metric_datapoint_optional_fields(self):
        """Test MetricDatapoint with only required fields."""
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        datapoint = MetricDatapoint(Timestamp=timestamp)
        assert datapoint.Timestamp == timestamp
        assert datapoint.Average is None
        assert datapoint.Sum is None


class TestMetricStatisticsResult:
    """Test MetricStatisticsResult model."""

    def test_metric_statistics_result_creation(self):
        """Test creating a MetricStatisticsResult."""
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        datapoint = MetricDatapoint(Timestamp=timestamp, Average=50.0)
        result = MetricStatisticsResult(Label='CPUUtilization', Datapoints=[datapoint])
        assert result.Label == 'CPUUtilization'
        assert len(result.Datapoints) == 1
        assert result.Datapoints[0].Average == 50.0


class TestFormatDimensions:
    """Test format_dimensions helper function."""

    def test_format_dimensions_none(self):
        """Test format_dimensions with None input."""
        result = format_dimensions(None)
        assert result is None

    def test_format_dimensions_empty_list(self):
        """Test format_dimensions with empty list."""
        result = format_dimensions([])
        assert result is None

    def test_format_dimensions_proper_format(self):
        """Test format_dimensions with properly formatted dimensions."""
        dimensions = [{'Name': 'DBInstanceIdentifier', 'Value': 'test-db'}]
        result = format_dimensions(dimensions)
        assert len(result) == 1
        assert result[0].Name == 'DBInstanceIdentifier'
        assert result[0].Value == 'test-db'

    def test_format_dimensions_key_value_format(self):
        """Test format_dimensions with key-value format."""
        dimensions = [{'DBInstanceIdentifier': 'test-db'}]
        result = format_dimensions(dimensions)
        assert len(result) == 1
        assert result[0].Name == 'DBInstanceIdentifier'
        assert result[0].Value == 'test-db'

    def test_format_dimensions_mixed_format(self):
        """Test format_dimensions with mixed formats."""
        dimensions = [{'Name': 'DBInstanceIdentifier', 'Value': 'test-db'}, {'Engine': 'mysql'}]
        result = format_dimensions(dimensions)
        assert len(result) == 2
        assert result[0].Name == 'DBInstanceIdentifier'
        assert result[0].Value == 'test-db'
        assert result[1].Name == 'Engine'
        assert result[1].Value == 'mysql'


class TestGetMetricStatistics:
    """Test get_metric_statistics tool."""

    @pytest.fixture
    def sample_response(self):
        """Sample CloudWatch response."""
        return {
            'Label': 'CPUUtilization',
            'Datapoints': [
                {'Timestamp': datetime(2024, 1, 1, 12, 0, 0), 'Average': 50.0, 'Unit': 'Percent'}
            ],
        }

    @pytest.mark.asyncio
    async def test_get_metric_statistics_basic(self, mock_cloudwatch_client, sample_response):
        """Test basic get_metric_statistics call."""
        mock_cloudwatch_client.get_metric_statistics.return_value = sample_response

        result = await _get_metric_statistics_core(
            metric_name='CPUUtilization',
            start_time='2024-01-01T11:00:00Z',
            end_time='2024-01-01T12:00:00Z',
            period=300,
        )

        assert isinstance(result, MetricStatisticsResult)
        assert result.Label == 'CPUUtilization'
        assert len(result.Datapoints) == 1
        assert result.Datapoints[0].Average == 50.0

    @pytest.mark.asyncio
    async def test_get_metric_statistics_with_dimensions(
        self, mock_cloudwatch_client, sample_response
    ):
        """Test get_metric_statistics with dimensions."""
        mock_cloudwatch_client.get_metric_statistics.return_value = sample_response

        dimensions = [{'Name': 'DBInstanceIdentifier', 'Value': 'test-db'}]
        await _get_metric_statistics_core(
            metric_name='CPUUtilization',
            start_time='2024-01-01T11:00:00Z',
            end_time='2024-01-01T12:00:00Z',
            period=300,
            dimensions=dimensions,
        )

        # Verify dimensions were passed to the client
        call_args = mock_cloudwatch_client.get_metric_statistics.call_args[1]
        assert 'Dimensions' in call_args
        assert call_args['Dimensions'][0]['Name'] == 'DBInstanceIdentifier'
        assert call_args['Dimensions'][0]['Value'] == 'test-db'

    @pytest.mark.asyncio
    async def test_get_metric_statistics_with_statistics(
        self, mock_cloudwatch_client, sample_response
    ):
        """Test get_metric_statistics with statistics."""
        mock_cloudwatch_client.get_metric_statistics.return_value = sample_response

        statistics = ['Average', 'Maximum']
        result = await _get_metric_statistics_core(
            metric_name='CPUUtilization',
            start_time='2024-01-01T11:00:00Z',
            end_time='2024-01-01T12:00:00Z',
            period=300,
            statistics=statistics,
        )

        # Verify statistics were passed to the client
        call_args = mock_cloudwatch_client.get_metric_statistics.call_args[1]
        assert 'Statistics' in call_args
        assert call_args['Statistics'] == ['Average', 'Maximum']
        assert isinstance(result, MetricStatisticsResult)

    @pytest.mark.asyncio
    async def test_get_metric_statistics_with_extended_statistics(
        self, mock_cloudwatch_client, sample_response
    ):
        """Test get_metric_statistics with extended statistics."""
        mock_cloudwatch_client.get_metric_statistics.return_value = sample_response

        extended_statistics = ['p50', 'p90']
        result = await _get_metric_statistics_core(
            metric_name='CPUUtilization',
            start_time='2024-01-01T11:00:00Z',
            end_time='2024-01-01T12:00:00Z',
            period=300,
            extended_statistics=extended_statistics,
        )

        # Verify extended statistics were passed to the client
        call_args = mock_cloudwatch_client.get_metric_statistics.call_args[1]
        assert 'ExtendedStatistics' in call_args
        assert call_args['ExtendedStatistics'] == ['p50', 'p90']
        assert isinstance(result, MetricStatisticsResult)

    @pytest.mark.asyncio
    async def test_get_metric_statistics_with_unit(self, mock_cloudwatch_client, sample_response):
        """Test get_metric_statistics with unit."""
        mock_cloudwatch_client.get_metric_statistics.return_value = sample_response

        result = await _get_metric_statistics_core(
            metric_name='CPUUtilization',
            start_time='2024-01-01T11:00:00Z',
            end_time='2024-01-01T12:00:00Z',
            period=300,
            unit='Percent',
        )

        # Verify unit was passed to the client
        call_args = mock_cloudwatch_client.get_metric_statistics.call_args[1]
        assert 'Unit' in call_args
        assert call_args['Unit'] == 'Percent'
        assert isinstance(result, MetricStatisticsResult)

    @pytest.mark.asyncio
    async def test_get_metric_statistics_custom_namespace(
        self, mock_cloudwatch_client, sample_response
    ):
        """Test get_metric_statistics with custom namespace."""
        mock_cloudwatch_client.get_metric_statistics.return_value = sample_response

        result = await _get_metric_statistics_core(
            metric_name='CPUUtilization',
            start_time='2024-01-01T11:00:00Z',
            end_time='2024-01-01T12:00:00Z',
            period=300,
            namespace='AWS/EC2',
        )

        # Verify namespace was passed to the client
        call_args = mock_cloudwatch_client.get_metric_statistics.call_args[1]
        assert call_args['Namespace'] == 'AWS/EC2'
        assert isinstance(result, MetricStatisticsResult)

    @pytest.mark.asyncio
    async def test_get_metric_statistics_empty_datapoints(self, mock_cloudwatch_client):
        """Test get_metric_statistics with empty datapoints."""
        empty_response = {'Label': 'CPUUtilization', 'Datapoints': []}
        mock_cloudwatch_client.get_metric_statistics.return_value = empty_response

        result = await _get_metric_statistics_core(
            metric_name='CPUUtilization',
            start_time='2024-01-01T11:00:00Z',
            end_time='2024-01-01T12:00:00Z',
            period=300,
        )

        assert isinstance(result, MetricStatisticsResult)
        assert result.Label == 'CPUUtilization'
        assert len(result.Datapoints) == 0
