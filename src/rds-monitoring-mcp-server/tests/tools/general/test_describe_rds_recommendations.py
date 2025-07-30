"""Tests for describe_rds_recommendations function."""

import pytest
from awslabs.rds_monitoring_mcp_server.tools.general.describe_rds_recommendations import (
    DBRecommendationList,
    describe_rds_recommendations,
)


class TestDescribeRDSRecommendations:
    """Test describe_rds_recommendations function."""

    @pytest.mark.asyncio
    async def test_with_status_filter(self, mock_rds_client, mock_handle_paginated_call):
        """Test describe_rds_recommendations with status filter."""
        mock_recommendations = []

        mock_handle_paginated_call.return_value = mock_recommendations

        result = await describe_rds_recommendations(status='active')

        assert result.count == 0
        assert len(result.recommendations) == 0

    @pytest.mark.asyncio
    async def test_with_severity_filter(self, mock_rds_client, mock_handle_paginated_call):
        """Test describe_rds_recommendations with severity filter."""
        mock_recommendations = []

        mock_handle_paginated_call.return_value = mock_recommendations

        result = await describe_rds_recommendations(severity='high')

        assert result.count == 0

    @pytest.mark.asyncio
    async def test_with_resource_filters(self, mock_rds_client, mock_handle_paginated_call):
        """Test describe_rds_recommendations with resource ID filters."""
        mock_recommendations = []

        mock_handle_paginated_call.return_value = mock_recommendations

        result = await describe_rds_recommendations(
            cluster_resource_id='cluster-123', dbi_resource_id='db-456'
        )

        assert result.count == 0

    @pytest.mark.asyncio
    async def test_with_time_filters(self, mock_rds_client, mock_handle_paginated_call):
        """Test describe_rds_recommendations with time filters."""
        mock_recommendations = []

        mock_handle_paginated_call.return_value = mock_recommendations

        result = await describe_rds_recommendations(
            last_updated_after='2023-01-01T00:00:00Z', last_updated_before='2023-01-31T23:59:59Z'
        )

        assert result.count == 0


class TestDBRecommendationList:
    """Test DBRecommendationList model."""

    def test_model_creation(self):
        """Test model creation with valid data."""
        recommendations = [
            {
                'RecommendationId': 'rec-1',
                'TypeRecommendation': 'performance',
                'Severity': 'high',
            }
        ]

        model = DBRecommendationList(recommendations=recommendations, count=1)

        assert model.count == 1
        assert len(model.recommendations) == 1
        assert model.recommendations[0]['RecommendationId'] == 'rec-1'
