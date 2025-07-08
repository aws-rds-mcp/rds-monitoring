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

"""Tests for find_slow_queries_and_wait_events tool."""

import json
import pytest
from awslabs.rds_monitoring_mcp_server.tools.db_instance.find_slow_queries_and_wait_events import (
    build_metric_queries,
    fetch_full_sql_text,
    find_slow_queries_and_wait_events,
    process_metric_results,
)
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


class TestBuildMetricQueries:
    """Tests for the build_metric_queries helper function."""

    def test_build_metric_queries_wait_events(self):
        """Test building metric queries for wait events."""
        result = build_metric_queries('db.wait_event', 'avg', 10)

        assert len(result) == 1
        assert result[0]['Metric'] == 'db.load.avg'
        assert result[0]['GroupBy']['Group'] == 'db.wait_event'
        assert result[0]['GroupBy']['Limit'] == 10

    def test_build_metric_queries_sql_tokenized(self):
        """Test building metric queries for SQL queries."""
        result = build_metric_queries('db.sql_tokenized', 'sum', 5)

        assert len(result) == 1
        assert result[0]['Metric'] == 'db.load.sum'
        assert result[0]['GroupBy']['Group'] == 'db.sql_tokenized'
        assert result[0]['GroupBy']['Limit'] == 5


class TestFetchFullSqlText:
    """Tests for the fetch_full_sql_text helper function."""

    def test_fetch_full_sql_text_success(self):
        """Test successfully fetching full SQL text."""
        mock_pi_client = MagicMock()
        mock_pi_client.get_dimension_key_details.return_value = {
            'Dimensions': {'sql-1': 'SELECT * FROM users WHERE id = ?'}
        }

        result = fetch_full_sql_text(
            pi_client=mock_pi_client,
            dbi_resource_identifier='db-123456',
            dimension='db.sql_tokenized',
            dimension_key='sql-1',
            dimension_value='SELECT * FROM users',
        )

        assert result == 'SELECT * FROM users WHERE id = ?'
        mock_pi_client.get_dimension_key_details.assert_called_once()

    def test_fetch_full_sql_text_error(self):
        """Test handling errors when fetching SQL text."""
        mock_pi_client = MagicMock()
        mock_pi_client.get_dimension_key_details.side_effect = Exception('API Error')
        tokenized_sql = 'SELECT * FROM users'

        result = fetch_full_sql_text(
            pi_client=mock_pi_client,
            dbi_resource_identifier='db-123456',
            dimension='db.sql_tokenized',
            dimension_key='sql-1',
            dimension_value=tokenized_sql,
        )

        assert result == tokenized_sql


class TestProcessMetricResults:
    """Tests for the process_metric_results helper function."""

    def test_process_metric_results_basic(self):
        """Test basic processing of metric results."""
        mock_pi_client = MagicMock()

        metric_list = [
            {
                'Key': {'Metric': 'db.load.avg', 'Dimensions': {'wait-1': 'IO:BufFileWrite'}},
                'DataPoints': [
                    {'Timestamp': datetime(2025, 6, 1, 12, 0, 0), 'Value': 2.5},
                    {'Timestamp': datetime(2025, 6, 1, 12, 5, 0), 'Value': 3.0},
                ],
            }
        ]

        results = process_metric_results(
            metric_list=metric_list,
            dimension='db.wait_event',
            full_sql_statement=False,
            pi_client=mock_pi_client,
            dbi_resource_identifier='db-123456',
        )

        assert len(results) == 1
        assert results[0].metric_name == 'db.load.avg'
        assert results[0].dimensions == {'wait-1': 'IO:BufFileWrite'}
        assert len(results[0].datapoints) == 2
        assert results[0].average_value == 2.75

    def test_process_metric_results_with_full_sql(self):
        """Test processing with full SQL text retrieval."""
        mock_pi_client = MagicMock()
        mock_pi_client.get_dimension_key_details.return_value = {
            'Dimensions': {'sql-1': 'SELECT * FROM users WHERE id = 123'}
        }

        metric_list = [
            {
                'Key': {'Metric': 'db.load.avg', 'Dimensions': {'sql-1': 'SELECT * FROM users'}},
                'DataPoints': [{'Timestamp': datetime(2025, 6, 1, 12, 0, 0), 'Value': 5.0}],
            }
        ]

        results = process_metric_results(
            metric_list=metric_list,
            dimension='db.sql_tokenized',
            full_sql_statement=True,
            pi_client=mock_pi_client,
            dbi_resource_identifier='db-123456',
        )

        assert len(results) == 1
        assert results[0].dimensions == {'sql-1': 'SELECT * FROM users WHERE id = 123'}

    def test_process_metric_results_sorting(self):
        """Test that results are sorted by average value in descending order."""
        mock_pi_client = MagicMock()

        metric_list = [
            {
                'Key': {'Metric': 'db.load.avg', 'Dimensions': {'wait-1': 'IO:BufFileWrite'}},
                'DataPoints': [{'Timestamp': datetime(2025, 6, 1, 12, 0, 0), 'Value': 1.0}],
            },
            {
                'Key': {'Metric': 'db.load.avg', 'Dimensions': {'wait-2': 'CPU'}},
                'DataPoints': [{'Timestamp': datetime(2025, 6, 1, 12, 0, 0), 'Value': 3.0}],
            },
            {
                'Key': {'Metric': 'db.load.avg', 'Dimensions': {'wait-3': 'Lock:tuple'}},
                'DataPoints': [{'Timestamp': datetime(2025, 6, 1, 12, 0, 0), 'Value': 2.0}],
            },
        ]

        results = process_metric_results(
            metric_list=metric_list,
            dimension='db.wait_event',
            full_sql_statement=False,
            pi_client=mock_pi_client,
            dbi_resource_identifier='db-123456',
        )

        assert len(results) == 3
        assert results[0].dimensions == {'wait-2': 'CPU'}
        assert results[1].dimensions == {'wait-3': 'Lock:tuple'}
        assert results[2].dimensions == {'wait-1': 'IO:BufFileWrite'}


class TestFindSlowQueriesAndWaitEvents:
    """Tests for the find_slow_queries_and_wait_events tool."""

    @pytest.mark.asyncio
    async def test_find_slow_queries_basic_execution(self, mock_pi_client):
        """Test basic execution of the find_slow_queries_and_wait_events tool."""
        test_dbi_resource_id = 'db-ABCDEFGHIJKLMNO123456'

        mock_pi_client.get_resource_metrics.return_value = {
            'MetricList': [
                {
                    'Key': {'Metric': 'db.load.avg', 'Dimensions': {'wait-1': 'IO:BufFileWrite'}},
                    'DataPoints': [
                        {'Timestamp': datetime(2025, 6, 1, 12, 0, 0), 'Value': 2.5},
                        {'Timestamp': datetime(2025, 6, 1, 12, 5, 0), 'Value': 3.0},
                    ],
                }
            ]
        }

        result_json = await find_slow_queries_and_wait_events(
            dbi_resource_identifier=test_dbi_resource_id,
            dimension='db.wait_event',
            calculation='avg',
            start_time='2025-06-01T12:00:00Z',
            end_time='2025-06-01T13:00:00Z',
            period_in_seconds=300,
        )

        result = json.loads(result_json)
        mock_pi_client.get_resource_metrics.assert_called_once()

        assert result['resource_identifier'] == test_dbi_resource_id
        assert result['dimension'] == 'db.wait_event'
        assert result['calculation'] == 'avg'
        assert result['period_seconds'] == 300
        assert result['count'] == 1

        metrics = result['results']
        assert len(metrics) == 1
        assert metrics[0]['metric_name'] == 'db.load.avg'
        assert metrics[0]['dimensions'] == {'wait-1': 'IO:BufFileWrite'}
        assert len(metrics[0]['datapoints']) == 2
        assert metrics[0]['average_value'] == 2.75

    @pytest.mark.asyncio
    async def test_find_slow_queries_with_full_sql(self, mock_pi_client):
        """Test find_slow_queries_and_wait_events with full SQL text."""
        test_dbi_resource_id = 'db-ABCDEFGHIJKLMNO123456'

        mock_pi_client.get_resource_metrics.return_value = {
            'MetricList': [
                {
                    'Key': {
                        'Metric': 'db.load.avg',
                        'Dimensions': {'sql-1': 'SELECT * FROM users'},
                    },
                    'DataPoints': [{'Timestamp': datetime(2025, 6, 1, 12, 0, 0), 'Value': 5.0}],
                }
            ]
        }

        mock_pi_client.get_dimension_key_details.return_value = {
            'Dimensions': {'sql-1': 'SELECT * FROM users WHERE id = 123'}
        }

        result_json = await find_slow_queries_and_wait_events(
            dbi_resource_identifier=test_dbi_resource_id,
            dimension='db.sql_tokenized',
            calculation='avg',
            start_time='2025-06-01T12:00:00Z',
            end_time='2025-06-01T13:00:00Z',
            full_sql_statement=True,
        )

        result = json.loads(result_json)

        assert 'dimension' in result, "Response missing 'dimension' key"
        assert result['dimension'] == 'db.sql_tokenized'

        metrics = result['results']
        assert len(metrics) == 1
        assert metrics[0]['dimensions'] == {'sql-1': 'SELECT * FROM users WHERE id = 123'}

    @pytest.mark.asyncio
    async def test_find_slow_queries_with_default_times(self, mock_pi_client):
        """Test find_slow_queries_and_wait_events with default time values."""
        test_dbi_resource_id = 'db-ABCDEFGHIJKLMNO123456'

        mock_pi_client.get_resource_metrics.return_value = {'MetricList': []}

        with patch('awslabs.rds_monitoring_mcp_server.common.utils.datetime') as mock_datetime:
            mock_now = datetime(2025, 6, 1, 12, 0, 0)
            mock_datetime.now.return_value = mock_now

            await find_slow_queries_and_wait_events(
                dbi_resource_identifier=test_dbi_resource_id,
                dimension='db.wait_event',
                calculation='avg',
            )

        mock_pi_client.get_resource_metrics.assert_called_once()

        call_kwargs = mock_pi_client.get_resource_metrics.call_args.kwargs
        assert 'StartTime' in call_kwargs
        assert 'EndTime' in call_kwargs

        start_time = call_kwargs['StartTime']
        end_time = call_kwargs['EndTime']
        assert end_time - start_time == timedelta(hours=1)

    @pytest.mark.asyncio
    async def test_find_slow_queries_custom_limit(self, mock_pi_client):
        """Test find_slow_queries_and_wait_events with custom result limit."""
        test_dbi_resource_id = 'db-ABCDEFGHIJKLMNO123456'
        custom_limit = 5

        mock_pi_client.get_resource_metrics.return_value = {'MetricList': []}

        await find_slow_queries_and_wait_events(
            dbi_resource_identifier=test_dbi_resource_id,
            dimension='db.wait_event',
            calculation='avg',
            limit=custom_limit,
        )

        mock_pi_client.get_resource_metrics.assert_called_once()

        call_args = mock_pi_client.get_resource_metrics.call_args
        call_kwargs = call_args.kwargs
        assert 'MetricQueries' in call_kwargs

        metric_queries = call_kwargs['MetricQueries']
        assert len(metric_queries) == 1
        assert metric_queries[0]['GroupBy']['Limit'] == custom_limit
