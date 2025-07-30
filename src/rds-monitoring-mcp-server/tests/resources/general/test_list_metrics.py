"""Tests for list_metrics functions."""

import pytest
from awslabs.rds_monitoring_mcp_server.resources.general.list_metrics import (
    MetricList,
    list_rds_metrics,
)


class TestMetricList:
    """Test MetricList model."""

    def test_model_creation(self):
        """Test model creation."""
        model = MetricList(metrics=['CPUUtilization'], count=1)
        assert model.metrics == ['CPUUtilization']
        assert model.count == 1
        assert model.namespace == 'AWS/RDS'


class TestListRDSMetrics:
    """Test list_rds_metrics function."""

    @pytest.mark.asyncio
    async def test_invalid_resource_type(self):
        """Test with invalid resource type."""
        result = await list_rds_metrics('invalid-type', 'test-resource')

        import json

        error_response = json.loads(result)
        assert 'error' in error_response
        assert 'Unsupported resource type: invalid-type' in error_response['error_message']

    @pytest.mark.asyncio
    async def test_valid_resource_types(self, mock_cloudwatch_client, mock_handle_paginated_call):
        """Test with valid resource types."""
        mock_handle_paginated_call.return_value = ['CPUUtilization']

        result1 = await list_rds_metrics('db-instance', 'test-instance')
        assert isinstance(result1, MetricList)

        result2 = await list_rds_metrics('db-cluster', 'test-cluster')
        assert isinstance(result2, MetricList)
