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

"""Tests for recommendations module."""

import json
import pytest
from awslabs.rds_monitoring_mcp_server.constants import PAGINATION_CONFIG
from awslabs.rds_monitoring_mcp_server.models import (
    DBRecommendation,
    RecommendedAction,
    SimplifiedMetric,
)
from awslabs.rds_monitoring_mcp_server.recommendations import (
    convert_action,
    convert_to_dbrecommendation,
    extract_metrics,
    get_recommendations,
)
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def sample_metrics() -> List[Dict[str, str]]:
    """Return sample metrics data for testing."""
    return [
        {
            'Name': 'CPUUtilization',
            'StatisticsDetails': 'Average: 85%, Max: 95% over the past 24 hours',
        },
        {
            'Name': 'FreeableMemory',
            'StatisticsDetails': 'Min: 500MB, Average: 750MB over the past 24 hours',
        },
    ]


@pytest.fixture
def action_dict_with_metrics(sample_metrics: List[Dict[str, str]]) -> Dict[str, Any]:
    """Return an action dictionary with metrics."""
    return {
        'Title': 'Scale up DB instance',
        'Description': 'The current instance size is too small for your workload',
        'IssueDetails': {'PerformanceIssueDetails': {'Metrics': sample_metrics}},
    }


@pytest.fixture
def action_dict_basic() -> Dict[str, str]:
    """Return a basic action dictionary without metrics."""
    return {
        'Title': 'Scale up DB instance',
        'Description': 'The current instance size is too small for your workload',
    }


@pytest.fixture
def recommendation_dict_basic() -> Dict[str, Any]:
    """Return a basic recommendation dictionary without actions."""
    return {
        'RecommendationId': 'rec-12345',
        'Severity': 'high',
        'Status': 'active',
        'CreatedTime': datetime(2023, 1, 1),
        'UpdatedTime': datetime(2023, 1, 2),
        'Detection': 'High CPU utilization detected',
        'Recommendation': 'Consider scaling up your instance',
        'Description': 'Your instance has been running at high CPU for the past 7 days',
        'Reason': 'Sustained high CPU utilization',
        'Category': 'performance efficiency',
        'Impact': 'Potential performance degradation',
    }


@pytest.fixture
def recommendation_dict_with_actions(
    action_dict_basic: Dict[str, str], sample_metrics: List[Dict[str, str]]
) -> Dict[str, Any]:
    """Return a recommendation dictionary with actions and metrics."""
    return {
        'RecommendationId': 'rec-12345',
        'Severity': 'high',
        'Status': 'active',
        'CreatedTime': datetime(2023, 1, 1),
        'UpdatedTime': datetime(2023, 1, 2),
        'RecommendedActions': [
            action_dict_basic,
            {
                'Title': 'Enable Performance Insights',
                'Description': 'Monitor performance metrics for deeper insights',
            },
        ],
        'IssueDetails': {'PerformanceIssueDetails': {'Metrics': sample_metrics}},
    }


@pytest.fixture
def mock_rds_client() -> MagicMock:
    """Return a mocked RDS client."""
    mock_client = MagicMock()
    mock_paginator = MagicMock()
    mock_client.get_paginator.return_value = mock_paginator

    mock_page_iterator = MagicMock()
    mock_paginator.paginate.return_value = mock_page_iterator

    return mock_client


class TestExtractMetrics:
    """Tests for the extract_metrics function."""

    def test_extract_metrics_with_metrics(self, action_dict_with_metrics: Dict[str, Any]) -> None:
        """Test extracting metrics when they are present in the action dictionary."""
        result = extract_metrics(action_dict_with_metrics)

        assert result is not None
        assert len(result) == 2
        assert result[0].name == 'CPUUtilization'
        assert result[0].statistics_details == 'Average: 85%, Max: 95% over the past 24 hours'
        assert result[1].name == 'FreeableMemory'
        assert result[1].statistics_details == 'Min: 500MB, Average: 750MB over the past 24 hours'

    def test_extract_metrics_without_metrics(self) -> None:
        """Test extracting metrics when performance issue details exist but no metrics."""
        action_dict = {'IssueDetails': {'PerformanceIssueDetails': {}}}

        result = extract_metrics(action_dict)

        assert result is None

    def test_extract_metrics_without_issue_details(self) -> None:
        """Test extracting metrics when no issue details exist."""
        action_dict = {}

        result = extract_metrics(action_dict)

        assert result is None

    def test_extract_metrics_with_empty_metrics(self) -> None:
        """Test extracting metrics when metrics list is empty."""
        action_dict = {'IssueDetails': {'PerformanceIssueDetails': {'Metrics': []}}}

        result = extract_metrics(action_dict)

        assert result is None

    def test_extract_metrics_with_incomplete_data(self) -> None:
        """Test extracting metrics when metrics have incomplete data."""
        action_dict = {
            'IssueDetails': {
                'PerformanceIssueDetails': {
                    'Metrics': [
                        {
                            'Name': 'CPUUtilization',
                        },
                        {'StatisticsDetails': 'Min: 500MB'},
                    ]
                }
            }
        }

        result = extract_metrics(action_dict)

        assert result == []


class TestConvertAction:
    """Tests for the convert_action function."""

    def test_convert_action_basic(self, action_dict_basic: Dict[str, str]) -> None:
        """Test basic conversion of action dict to RecommendedAction model."""
        result = convert_action(action_dict_basic)

        assert isinstance(result, RecommendedAction)
        assert result.title == 'Scale up DB instance'
        assert result.description == 'The current instance size is too small for your workload'
        assert result.relevant_metrics is None

    def test_convert_action_with_metrics(self, action_dict_basic: Dict[str, str]) -> None:
        """Test conversion of action dict with metrics to RecommendedAction model."""
        metrics = [
            SimplifiedMetric(
                name='CPUUtilization',
                statistics_details='Average: 85%, Max: 95% over the past 24 hours',
            )
        ]

        result = convert_action(action_dict_basic, metrics)

        assert isinstance(result, RecommendedAction)
        assert result.title == 'Scale up DB instance'
        assert result.description == 'The current instance size is too small for your workload'
        assert result.relevant_metrics is not None
        assert len(result.relevant_metrics) == 1
        assert result.relevant_metrics[0].name == 'CPUUtilization'

    def test_convert_action_with_missing_fields(self) -> None:
        """Test conversion of action dict with missing fields."""
        action_dict = {}

        result = convert_action(action_dict)

        assert isinstance(result, RecommendedAction)
        assert result.title == ''
        assert result.description is None
        assert result.relevant_metrics is None


class TestConvertToDBRecommendation:
    """Tests for the convert_to_dbrecommendation function."""

    def test_convert_to_dbrecommendation_basic(
        self, recommendation_dict_basic: Dict[str, Any]
    ) -> None:
        """Test basic conversion of recommendation dict to DBRecommendation model."""
        result = convert_to_dbrecommendation(recommendation_dict_basic)

        assert isinstance(result, DBRecommendation)
        assert result.recommendation_id == 'rec-12345'
        assert result.severity == 'high'
        assert result.status == 'active'
        assert result.created_time == '2023-01-01T00:00:00'
        assert result.updated_time == '2023-01-02T00:00:00'
        assert result.detection == 'High CPU utilization detected'
        assert result.recommendation == 'Consider scaling up your instance'
        assert (
            result.description == 'Your instance has been running at high CPU for the past 7 days'
        )
        assert result.reason == 'Sustained high CPU utilization'
        assert result.category == 'performance efficiency'
        assert result.impact == 'Potential performance degradation'
        assert result.recommended_actions is None

    def test_convert_to_dbrecommendation_with_actions(
        self, recommendation_dict_with_actions: Dict[str, Any]
    ) -> None:
        """Test conversion of recommendation dict with actions to DBRecommendation model."""
        result = convert_to_dbrecommendation(recommendation_dict_with_actions)

        assert isinstance(result, DBRecommendation)
        assert result.recommendation_id == 'rec-12345'
        assert result.recommended_actions is not None
        assert len(result.recommended_actions) == 2
        assert result.recommended_actions[0].title == 'Scale up DB instance'
        assert result.recommended_actions[1].title == 'Enable Performance Insights'
        # Metrics from the main recommendation should be passed to the actions
        assert result.recommended_actions[0].relevant_metrics is not None
        assert len(result.recommended_actions[0].relevant_metrics) == 2
        assert result.recommended_actions[0].relevant_metrics[0].name == 'CPUUtilization'

    def test_convert_to_dbrecommendation_with_action_specific_metrics(self) -> None:
        """Test conversion with action-specific metrics taking precedence over recommendation metrics."""
        recommendation_dict = {
            'RecommendationId': 'rec-12345',
            'Severity': 'high',
            'Status': 'active',
            'CreatedTime': datetime(2023, 1, 1),
            'UpdatedTime': datetime(2023, 1, 2),
            'RecommendedActions': [
                {
                    'Title': 'Scale up DB instance',
                    'Description': 'The current instance size is too small for your workload',
                    'IssueDetails': {
                        'PerformanceIssueDetails': {
                            'Metrics': [
                                {
                                    'Name': 'ActionSpecificMetric',
                                    'StatisticsDetails': 'This metric is specific to the action',
                                }
                            ]
                        }
                    },
                }
            ],
            'IssueDetails': {
                'PerformanceIssueDetails': {
                    'Metrics': [
                        {
                            'Name': 'CPUUtilization',
                            'StatisticsDetails': 'Average: 85%, Max: 95% over the past 24 hours',
                        }
                    ]
                }
            },
        }

        result = convert_to_dbrecommendation(recommendation_dict)

        assert isinstance(result, DBRecommendation)
        assert result.recommendation_id == 'rec-12345'
        assert result.recommended_actions is not None
        assert len(result.recommended_actions) == 1
        # Action should have its own metrics rather than the recommendation's metrics
        assert result.recommended_actions[0].relevant_metrics is not None
        assert len(result.recommended_actions[0].relevant_metrics) == 1
        assert result.recommended_actions[0].relevant_metrics[0].name == 'ActionSpecificMetric'


class TestGetRecommendations:
    """Tests for the get_recommendations function."""

    @pytest.mark.asyncio
    async def test_get_recommendations_basic(self, mock_rds_client: MagicMock) -> None:
        """Test basic retrieval of recommendations."""
        mock_page_iterator = mock_rds_client.get_paginator.return_value.paginate.return_value
        mock_page_iterator.__iter__.return_value = [
            {
                'DBRecommendations': [
                    {
                        'RecommendationId': 'rec-12345',
                        'Severity': 'high',
                        'Status': 'active',
                        'CreatedTime': datetime(2023, 1, 1),
                        'UpdatedTime': datetime(2023, 1, 2),
                    }
                ]
            }
        ]

        result = await get_recommendations(mock_rds_client)

        mock_rds_client.get_paginator.assert_called_once_with('describe_db_recommendations')
        mock_rds_client.get_paginator.return_value.paginate.assert_called_once_with(
            PaginationConfig=PAGINATION_CONFIG
        )

        result_dict = json.loads(result)

        assert isinstance(result, str)
        assert result_dict['count'] == 1
        assert len(result_dict['recommendations']) == 1
        assert result_dict['recommendations'][0]['recommendation_id'] == 'rec-12345'
        assert result_dict['recommendations'][0]['severity'] == 'high'
        assert result_dict['recommendations'][0]['status'] == 'active'
        assert 'created_time' in result_dict['recommendations'][0]
        assert 'updated_time' in result_dict['recommendations'][0]

    @pytest.mark.asyncio
    async def test_get_recommendations_with_filters(self, mock_rds_client: MagicMock) -> None:
        """Test retrieval of recommendations with filters."""
        mock_page_iterator = mock_rds_client.get_paginator.return_value.paginate.return_value
        mock_page_iterator.__iter__.return_value = [
            {
                'DBRecommendations': [
                    {
                        'RecommendationId': 'rec-12345',
                        'Severity': 'high',
                        'Status': 'active',
                        'CreatedTime': datetime(2023, 1, 1),
                        'UpdatedTime': datetime(2023, 1, 2),
                    }
                ]
            }
        ]

        last_updated_after = datetime(2023, 1, 1)
        last_updated_before = datetime(2023, 1, 5)
        status = 'active'
        severity = 'high'
        cluster_resource_id = 'cluster-12345'
        dbi_resource_id = 'db-12345'

        result = await get_recommendations(
            mock_rds_client,
            last_updated_after=last_updated_after,
            last_updated_before=last_updated_before,
            status=status,
            severity=severity,
            cluster_resource_id=cluster_resource_id,
            dbi_resource_id=dbi_resource_id,
        )

        mock_rds_client.get_paginator.return_value.paginate.assert_called_once()
        call_kwargs = mock_rds_client.get_paginator.return_value.paginate.call_args[1]

        assert call_kwargs['LastUpdatedAfter'] == last_updated_after
        assert call_kwargs['LastUpdatedBefore'] == last_updated_before

        filters = call_kwargs['Filters']
        assert len(filters) == 4  # status, severity, cluster, dbi

        filter_dict = {f['Name']: f['Values'] for f in filters}
        assert filter_dict['status'] == ['active']
        assert filter_dict['severity'] == ['high']
        assert filter_dict['cluster-resource-id'] == ['cluster-12345']
        assert filter_dict['dbi-resource-id'] == ['db-12345']

        result_dict = json.loads(result)
        assert result_dict['count'] == 1
        assert len(result_dict['recommendations']) == 1

    @pytest.mark.asyncio
    async def test_get_recommendations_with_empty_response(
        self, mock_rds_client: MagicMock
    ) -> None:
        """Test retrieval of recommendations when API returns empty response."""
        mock_page_iterator = mock_rds_client.get_paginator.return_value.paginate.return_value
        mock_page_iterator.__iter__.return_value = [{'DBRecommendations': []}]

        result = await get_recommendations(mock_rds_client)

        result_dict = json.loads(result)
        assert result_dict['count'] == 0
        assert len(result_dict['recommendations']) == 0

    @pytest.mark.asyncio
    async def test_get_recommendations_multiple_pages(self, mock_rds_client: MagicMock) -> None:
        """Test retrieval of recommendations with multiple pages of results."""
        mock_page_iterator = mock_rds_client.get_paginator.return_value.paginate.return_value
        mock_page_iterator.__iter__.return_value = [
            {
                'DBRecommendations': [
                    {
                        'RecommendationId': 'rec-1',
                        'Severity': 'high',
                        'Status': 'active',
                        'CreatedTime': datetime(2023, 1, 1),
                        'UpdatedTime': datetime(2023, 1, 2),
                    }
                ]
            },
            {
                'DBRecommendations': [
                    {
                        'RecommendationId': 'rec-2',
                        'Severity': 'medium',
                        'Status': 'active',
                        'CreatedTime': datetime(2023, 1, 3),
                        'UpdatedTime': datetime(2023, 1, 4),
                    }
                ]
            },
        ]

        result = await get_recommendations(mock_rds_client)

        result_dict = json.loads(result)
        assert result_dict['count'] == 2
        assert len(result_dict['recommendations']) == 2
        assert result_dict['recommendations'][0]['recommendation_id'] == 'rec-1'
        assert result_dict['recommendations'][0]['severity'] == 'high'
        assert result_dict['recommendations'][1]['recommendation_id'] == 'rec-2'
        assert result_dict['recommendations'][1]['severity'] == 'medium'

    @pytest.mark.asyncio
    async def test_get_recommendations_with_exception(self, mock_rds_client: MagicMock) -> None:
        """Test handling of exceptions during retrieval of recommendations."""
        mock_rds_client.get_paginator.return_value.paginate.side_effect = Exception('API Error')

        mock_error_dict = {'recommendations': [], 'count': 0}

        with patch(
            'awslabs.rds_monitoring_mcp_server.recommendations.handle_aws_error',
            AsyncMock(return_value=mock_error_dict),
        ) as mock_handle_error:
            result = await get_recommendations(mock_rds_client)

            mock_handle_error.assert_called_once()
            assert mock_handle_error.call_args.args[0] == 'describe_db_recommendations'
            assert isinstance(mock_handle_error.call_args.args[1], Exception)

            result_dict = json.loads(result)
            assert result_dict['count'] == 0
            assert len(result_dict['recommendations']) == 0
