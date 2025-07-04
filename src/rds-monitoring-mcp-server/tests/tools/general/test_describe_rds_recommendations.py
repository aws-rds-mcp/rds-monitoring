"""Tests for the describe_rds_recommendations module."""

import json
import pytest
from awslabs.rds_monitoring_mcp_server.common.utils import convert_datetime_to_string
from awslabs.rds_monitoring_mcp_server.tools.general.describe_rds_recommendations import (
    SimplifiedMetric,
    convert_action,
    convert_to_dbrecommendation,
    describe_rds_recommendations,
    extract_metrics,
)
from datetime import datetime, timezone
from mypy_boto3_rds.type_defs import DBRecommendationTypeDef, RecommendedActionTypeDef


def create_test_recommendation() -> DBRecommendationTypeDef:
    """Create a sample recommendation for testing."""
    return {
        'RecommendationId': 'test-rec-id',
        'Severity': 'high',
        'Status': 'active',
        'CreatedTime': datetime(2025, 1, 1, tzinfo=timezone.utc),
        'UpdatedTime': datetime(2025, 1, 2, tzinfo=timezone.utc),
        'Detection': 'Test detection',
        'Recommendation': 'Test recommendation',
        'Description': 'Test description',
        'Reason': 'Test reason',
        'Category': 'performance efficiency',
        'Impact': 'Test impact',
        'RecommendedActions': [
            {
                'Title': 'Test action',
                'Description': 'Test action description',
                'IssueDetails': {
                    'PerformanceIssueDetails': {
                        'Metrics': [
                            {
                                'Name': 'CPUUtilization',
                                'StatisticsDetails': 'High CPU usage detected',
                            }
                        ]
                    }
                },
            }
        ],
    }


def create_test_action() -> RecommendedActionTypeDef:
    """Create a sample action for testing."""
    return {
        'Title': 'Test action',
        'Description': 'Test action description',
        'IssueDetails': {
            'PerformanceIssueDetails': {
                'Metrics': [
                    {
                        'Name': 'CPUUtilization',
                        'StatisticsDetails': 'High CPU usage detected',
                    }
                ]
            }
        },
    }


class TestHelperFunctions:
    """Tests for helper functions in the describe_rds_recommendations module."""

    def test_extract_metrics(self):
        """Test the extract_metrics function."""
        action = create_test_action()
        metrics = extract_metrics(action)

        assert metrics is not None
        assert len(metrics) == 1
        assert metrics[0].name == 'CPUUtilization'
        assert metrics[0].statistics_details == 'High CPU usage detected'

        action = {'IssueDetails': {'PerformanceIssueDetails': {'Metrics': []}}}
        metrics = extract_metrics(action)
        assert metrics is None

        action = {'Title': 'Test action'}
        metrics = extract_metrics(action)
        assert metrics is None

    def test_convert_action(self):
        """Test the convert_action function."""
        action_dict = create_test_action()
        metrics = [
            SimplifiedMetric(name='CPUUtilization', statistics_details='High CPU usage detected')
        ]

        action = convert_action(action_dict, metrics)
        assert action.title == 'Test action'
        assert action.description == 'Test action description'
        assert len(action.relevant_metrics) == 1
        assert action.relevant_metrics[0].name == 'CPUUtilization'

        action = convert_action(action_dict)
        assert action.title == 'Test action'
        assert action.description == 'Test action description'
        assert action.relevant_metrics is None

    def test_convert_to_dbrecommendation(self):
        """Test the convert_to_dbrecommendation function."""
        rec_dict = create_test_recommendation()

        recommendation = convert_to_dbrecommendation(rec_dict)

        assert recommendation.recommendation_id == 'test-rec-id'
        assert recommendation.severity == 'high'
        assert recommendation.status == 'active'
        assert recommendation.created_time == convert_datetime_to_string(rec_dict['CreatedTime'])
        assert recommendation.updated_time == convert_datetime_to_string(rec_dict['UpdatedTime'])
        assert recommendation.detection == 'Test detection'
        assert recommendation.recommendation == 'Test recommendation'
        assert recommendation.description == 'Test description'
        assert recommendation.reason == 'Test reason'
        assert recommendation.category == 'performance efficiency'
        assert recommendation.impact == 'Test impact'

        assert len(recommendation.recommended_actions) == 1
        action = recommendation.recommended_actions[0]
        assert action.title == 'Test action'
        assert action.description == 'Test action description'

        assert action.relevant_metrics is not None
        assert len(action.relevant_metrics) == 1
        assert action.relevant_metrics[0].name == 'CPUUtilization'
        assert action.relevant_metrics[0].statistics_details == 'High CPU usage detected'

        rec_dict['RecommendedActions'] = [{'Title': '', 'Description': None}]
        recommendation = convert_to_dbrecommendation(rec_dict)
        assert len(recommendation.recommended_actions) == 1


class TestDescribeRDSRecommendations:
    """Tests for the describe_rds_recommendations function."""

    @pytest.mark.asyncio
    async def test_describe_rds_recommendations_no_filters(self, mock_rds_client):
        """Test the describe_rds_recommendations function with no filters."""
        mock_rds_client.get_paginator.return_value.paginate.return_value = [
            {'DBRecommendations': [create_test_recommendation()]}
        ]

        result = await describe_rds_recommendations()

        mock_rds_client.get_paginator.assert_called_once_with('describe_db_recommendations')
        mock_rds_client.get_paginator.return_value.paginate.assert_called_once()

        result_dict = json.loads(result)
        assert result_dict['count'] == 1
        assert len(result_dict['recommendations']) == 1

        recommendation = result_dict['recommendations'][0]
        assert recommendation['recommendation_id'] == 'test-rec-id'
        assert recommendation['severity'] == 'high'
        assert recommendation['status'] == 'active'

    @pytest.mark.asyncio
    async def test_describe_rds_recommendations_with_filters(self, mock_rds_client):
        """Test the describe_rds_recommendations function with filters."""
        mock_rds_client.get_paginator.return_value.paginate.return_value = [
            {'DBRecommendations': [create_test_recommendation()]}
        ]

        await describe_rds_recommendations(
            last_updated_after='2025-01-01T00:00:00Z',
            last_updated_before='2025-01-02T00:00:00Z',
            status='active',
            severity='high',
            cluster_resource_id='test-cluster',
            dbi_resource_id='test-instance',
        )

        mock_rds_client.get_paginator.assert_called_once_with('describe_db_recommendations')
        mock_rds_client.get_paginator.return_value.paginate.assert_called_once()

        paginate_kwargs = mock_rds_client.get_paginator.return_value.paginate.call_args[1]
        assert paginate_kwargs['LastUpdatedAfter'] == '2025-01-01T00:00:00Z'
        assert paginate_kwargs['LastUpdatedBefore'] == '2025-01-02T00:00:00Z'

        filters = paginate_kwargs['Filters']
        assert {'Name': 'status', 'Values': ['active']} in filters
        assert {'Name': 'severity', 'Values': ['high']} in filters
        assert {'Name': 'cluster-resource-id', 'Values': ['test-cluster']} in filters
        assert {'Name': 'dbi-resource-id', 'Values': ['test-instance']} in filters

    @pytest.mark.asyncio
    async def test_describe_rds_recommendations_pagination(self, mock_rds_client):
        """Test the describe_rds_recommendations function with pagination."""
        rec1 = create_test_recommendation()
        rec1['RecommendationId'] = 'test-rec-1'

        rec2 = create_test_recommendation()
        rec2['RecommendationId'] = 'test-rec-2'

        mock_rds_client.get_paginator.return_value.paginate.return_value = [
            {'DBRecommendations': [rec1]},
            {'DBRecommendations': [rec2]},
        ]

        result = await describe_rds_recommendations()

        result_dict = json.loads(result)
        assert result_dict['count'] == 2
        assert len(result_dict['recommendations']) == 2

        rec_ids = [rec['recommendation_id'] for rec in result_dict['recommendations']]
        assert 'test-rec-1' in rec_ids
        assert 'test-rec-2' in rec_ids

    @pytest.mark.asyncio
    async def test_describe_rds_recommendations_empty_result(self, mock_rds_client):
        """Test the describe_rds_recommendations function with empty results."""
        mock_rds_client.get_paginator.return_value.paginate.return_value = [
            {'DBRecommendations': []}
        ]

        result = await describe_rds_recommendations()

        result_dict = json.loads(result)
        assert result_dict['count'] == 0
        assert len(result_dict['recommendations']) == 0

    @pytest.mark.asyncio
    async def test_describe_rds_recommendations_with_empty_actions(self, mock_rds_client):
        """Test the describe_rds_recommendations function with empty actions."""
        rec = create_test_recommendation()
        rec['RecommendedActions'] = [{'Title': '', 'Description': None}]

        mock_rds_client.get_paginator.return_value.paginate.return_value = [
            {'DBRecommendations': [rec]}
        ]

        result = await describe_rds_recommendations()

        result_dict = json.loads(result)
        assert result_dict['count'] == 1
        assert len(result_dict['recommendations']) == 1

        recommendation = result_dict['recommendations'][0]
        assert len(recommendation['recommended_actions']) == 1
