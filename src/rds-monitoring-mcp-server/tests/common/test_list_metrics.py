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

"""Tests for the list_metrics helper function."""

import pytest
from awslabs.rds_monitoring_mcp_server.common.list_metrics import ListMetricItem, list_metrics
from unittest.mock import MagicMock


@pytest.mark.asyncio
async def test_list_metrics_basic(mock_cloudwatch_client):
    """Test that list_metrics correctly formats and returns metrics."""
    mock_all_metrics = {
        'Metrics': [
            {
                'MetricName': 'CPUUtilization',
                'Dimensions': [{'Name': 'DBInstanceIdentifier', 'Value': 'db-instance-1'}],
            },
            {
                'MetricName': 'DatabaseConnections',
                'Dimensions': [{'Name': 'DBInstanceIdentifier', 'Value': 'db-instance-1'}],
            },
            {
                'MetricName': 'FreeStorageSpace',
                'Dimensions': [{'Name': 'DBInstanceIdentifier', 'Value': 'db-instance-1'}],
            },
        ]
    }

    mock_recent_metrics = {
        'Metrics': [
            {
                'MetricName': 'CPUUtilization',
                'Dimensions': [{'Name': 'DBInstanceIdentifier', 'Value': 'db-instance-1'}],
            },
            {
                'MetricName': 'DatabaseConnections',
                'Dimensions': [{'Name': 'DBInstanceIdentifier', 'Value': 'db-instance-1'}],
            },
        ]
    }

    mock_paginator = MagicMock()
    mock_all_iterator = MagicMock()
    mock_all_iterator.paginate.return_value = [mock_all_metrics]

    mock_recent_iterator = MagicMock()
    mock_recent_iterator.paginate.return_value = [mock_recent_metrics]

    mock_paginator.paginate.side_effect = [
        mock_all_iterator.paginate(),
        mock_recent_iterator.paginate(),
    ]

    mock_cloudwatch_client.get_paginator.return_value = mock_paginator

    results = await list_metrics('DBInstanceIdentifier', 'db-instance-1')

    assert len(results) == 3
    assert all(isinstance(item, ListMetricItem) for item in results)

    metric_map = {item.metric_name: item.recently_published_data_points for item in results}
    assert metric_map['CPUUtilization'] is True
    assert metric_map['DatabaseConnections'] is True
    assert metric_map['FreeStorageSpace'] is False

    mock_cloudwatch_client.get_paginator.assert_called_once_with('list_metrics')

    paginate_calls = mock_paginator.paginate.call_args_list
    assert len(paginate_calls) == 2

    assert paginate_calls[0][1]['Namespace'] == 'AWS/RDS'
    assert paginate_calls[0][1]['Dimensions'] == [
        {'Name': 'DBInstanceIdentifier', 'Value': 'db-instance-1'}
    ]
    assert 'RecentlyActive' not in paginate_calls[0][1]

    assert paginate_calls[1][1]['Namespace'] == 'AWS/RDS'
    assert paginate_calls[1][1]['Dimensions'] == [
        {'Name': 'DBInstanceIdentifier', 'Value': 'db-instance-1'}
    ]
    assert paginate_calls[1][1]['RecentlyActive'] == 'PT3H'


@pytest.mark.asyncio
async def test_list_metrics_pagination(mock_cloudwatch_client):
    """Test that list_metrics correctly handles pagination."""
    mock_all_metrics_page1 = {
        'Metrics': [
            {
                'MetricName': 'Metric1',
                'Dimensions': [{'Name': 'DBClusterIdentifier', 'Value': 'db-cluster-1'}],
            },
            {
                'MetricName': 'Metric2',
                'Dimensions': [{'Name': 'DBClusterIdentifier', 'Value': 'db-cluster-1'}],
            },
        ]
    }

    mock_all_metrics_page2 = {
        'Metrics': [
            {
                'MetricName': 'Metric3',
                'Dimensions': [{'Name': 'DBClusterIdentifier', 'Value': 'db-cluster-1'}],
            },
            {
                'MetricName': 'Metric4',
                'Dimensions': [{'Name': 'DBClusterIdentifier', 'Value': 'db-cluster-1'}],
            },
        ]
    }

    mock_recent_metrics_page1 = {
        'Metrics': [
            {
                'MetricName': 'Metric1',
                'Dimensions': [{'Name': 'DBClusterIdentifier', 'Value': 'db-cluster-1'}],
            },
        ]
    }

    mock_recent_metrics_page2 = {
        'Metrics': [
            {
                'MetricName': 'Metric3',
                'Dimensions': [{'Name': 'DBClusterIdentifier', 'Value': 'db-cluster-1'}],
            },
        ]
    }

    mock_paginator = MagicMock()
    mock_all_iterator = MagicMock()
    mock_all_iterator.paginate.return_value = [mock_all_metrics_page1, mock_all_metrics_page2]

    mock_recent_iterator = MagicMock()
    mock_recent_iterator.paginate.return_value = [
        mock_recent_metrics_page1,
        mock_recent_metrics_page2,
    ]

    mock_paginator.paginate.side_effect = [
        mock_all_iterator.paginate(),
        mock_recent_iterator.paginate(),
    ]

    mock_cloudwatch_client.get_paginator.return_value = mock_paginator

    results = await list_metrics('DBClusterIdentifier', 'db-cluster-1')

    assert len(results) == 4

    metric_map = {item.metric_name: item.recently_published_data_points for item in results}
    assert metric_map['Metric1'] is True
    assert metric_map['Metric2'] is False
    assert metric_map['Metric3'] is True
    assert metric_map['Metric4'] is False


@pytest.mark.asyncio
async def test_list_metrics_no_metrics(mock_cloudwatch_client):
    """Test that list_metrics handles the case when no metrics are returned."""
    mock_all_metrics = {'Metrics': []}
    mock_recent_metrics = {'Metrics': []}

    mock_paginator = MagicMock()
    mock_all_iterator = MagicMock()
    mock_all_iterator.paginate.return_value = [mock_all_metrics]

    mock_recent_iterator = MagicMock()
    mock_recent_iterator.paginate.return_value = [mock_recent_metrics]

    mock_paginator.paginate.side_effect = [
        mock_all_iterator.paginate(),
        mock_recent_iterator.paginate(),
    ]

    mock_cloudwatch_client.get_paginator.return_value = mock_paginator

    results = await list_metrics('DBInstanceIdentifier', 'non-existent-instance')
    assert len(results) == 0


@pytest.mark.asyncio
async def test_list_metrics_duplicate_handling(mock_cloudwatch_client):
    """Test that list_metrics correctly handles duplicate metrics."""
    mock_all_metrics = {
        'Metrics': [
            {
                'MetricName': 'CPUUtilization',
                'Dimensions': [{'Name': 'DBInstanceIdentifier', 'Value': 'db-instance-1'}],
            },
            {
                'MetricName': 'CPUUtilization',
                'Dimensions': [{'Name': 'DBInstanceIdentifier', 'Value': 'db-instance-1'}],
            },
            {
                'MetricName': 'DatabaseConnections',
                'Dimensions': [{'Name': 'DBInstanceIdentifier', 'Value': 'db-instance-1'}],
            },
        ]
    }

    mock_recent_metrics = {
        'Metrics': [
            {
                'MetricName': 'CPUUtilization',
                'Dimensions': [{'Name': 'DBInstanceIdentifier', 'Value': 'db-instance-1'}],
            },
        ]
    }

    mock_paginator = MagicMock()
    mock_all_iterator = MagicMock()
    mock_all_iterator.paginate.return_value = [mock_all_metrics]

    mock_recent_iterator = MagicMock()
    mock_recent_iterator.paginate.return_value = [mock_recent_metrics]

    mock_paginator.paginate.side_effect = [
        mock_all_iterator.paginate(),
        mock_recent_iterator.paginate(),
    ]

    mock_cloudwatch_client.get_paginator.return_value = mock_paginator

    results = await list_metrics('DBInstanceIdentifier', 'db-instance-1')

    assert len(results) == 3

    metric_counts = {}
    for item in results:
        metric_counts[item.metric_name] = metric_counts.get(item.metric_name, 0) + 1

    assert metric_counts['CPUUtilization'] == 2
    assert metric_counts['DatabaseConnections'] == 1
