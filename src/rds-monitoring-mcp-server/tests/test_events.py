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

"""Tests for RDS Management MCP Server events module."""

import json
import pytest
from awslabs.rds_monitoring_mcp_server.events import describe_rds_events, format_event
from awslabs.rds_monitoring_mcp_server.models import DBEvent
from botocore.exceptions import ClientError
from datetime import datetime
from mypy_boto3_rds.type_defs import EventTypeDef
from typing import cast
from unittest.mock import patch


class TestFormatEvent:
    """Tests for format_event function."""

    def test_format_event_complete(self):
        """Test formatting an event with all fields present."""
        current_time = datetime.now()
        mock_event = cast(
            EventTypeDef,
            {
                'SourceIdentifier': 'test-instance',
                'SourceType': 'db-instance',
                'Message': 'This is a test event',
                'EventCategories': ['backup', 'recovery'],
                'Date': current_time,
                'SourceArn': 'arn:aws:rds:us-east-1:123456789012:db:test-instance',
            },
        )

        result = format_event(mock_event)

        assert isinstance(result, DBEvent)
        assert result.message == 'This is a test event'
        assert result.event_categories == ['backup', 'recovery']
        assert result.date == current_time.isoformat()
        assert result.source_arn == 'arn:aws:rds:us-east-1:123456789012:db:test-instance'

    def test_format_event_missing_fields(self):
        """Test formatting an event with missing fields."""
        mock_event = cast(
            EventTypeDef,
            {
                'Message': 'Event with missing fields',
                'SourceIdentifier': 'test-instance',
                'SourceType': 'db-instance',
            },
        )

        result = format_event(mock_event)

        assert isinstance(result, DBEvent)
        assert result.message == 'Event with missing fields'
        assert result.event_categories == []
        assert result.date == ''
        assert result.source_arn is None

    def test_format_event_string_date(self):
        """Test formatting an event with a string date."""
        mock_event = cast(
            EventTypeDef,
            {
                'SourceIdentifier': 'test-instance',
                'SourceType': 'db-instance',
                'Message': 'Event with string date',
                'EventCategories': ['configuration change'],
                'Date': '2025-06-25T14:30:00.000Z',
                'SourceArn': 'arn:aws:rds:us-east-1:123456789012:db:test-instance',
            },
        )

        result = format_event(mock_event)

        assert isinstance(result, DBEvent)
        assert result.message == 'Event with string date'
        assert result.event_categories == ['configuration change']
        assert result.date == '2025-06-25T14:30:00.000Z'
        assert result.source_arn == 'arn:aws:rds:us-east-1:123456789012:db:test-instance'

    def test_format_event_none_date(self):
        """Test formatting an event with None date."""
        mock_event = cast(
            EventTypeDef,
            {
                'SourceIdentifier': 'test-instance',
                'SourceType': 'db-instance',
                'Message': 'Event with None date',
                'EventCategories': ['configuration change'],
                'Date': None,
                'SourceArn': 'arn:aws:rds:us-east-1:123456789012:db:test-instance',
            },
        )

        result = format_event(mock_event)

        assert isinstance(result, DBEvent)
        assert result.message == 'Event with None date'
        assert result.event_categories == ['configuration change']
        assert result.date == ''
        assert result.source_arn == 'arn:aws:rds:us-east-1:123456789012:db:test-instance'


@pytest.mark.asyncio
class TestDescribeDBEvents:
    """Tests for describe_rds_events function."""

    async def test_describe_rds_events_success(self, mock_rds_client):
        """Test successful event retrieval."""
        current_time = datetime.now()
        mock_events = [
            {
                'SourceIdentifier': 'test-instance',
                'SourceType': 'db-instance',
                'Message': 'DB instance started',
                'EventCategories': ['availability'],
                'Date': current_time,
                'SourceArn': 'arn:aws:rds:us-east-1:123456789012:db:test-instance',
            },
            {
                'SourceIdentifier': 'test-instance',
                'SourceType': 'db-instance',
                'Message': 'DB instance stopped',
                'EventCategories': ['availability'],
                'Date': current_time,
                'SourceArn': 'arn:aws:rds:us-east-1:123456789012:db:test-instance',
            },
        ]
        mock_rds_client.describe_events.return_value = {'Events': mock_events}

        result = await describe_rds_events(
            rds_client=mock_rds_client,
            source_identifier='test-instance',
            source_type='db-instance',
        )

        mock_rds_client.describe_events.assert_called_once_with(
            SourceIdentifier='test-instance',
            SourceType='db-instance',
            MaxRecords=100,  # From constants.MAX_ITEMS
        )

        result_dict = json.loads(result)
        assert result_dict['source_identifier'] == 'test-instance'
        assert result_dict['source_type'] == 'db-instance'
        assert result_dict['count'] == 2
        assert len(result_dict['events']) == 2
        assert result_dict['events'][0]['message'] == 'DB instance started'
        assert result_dict['events'][1]['message'] == 'DB instance stopped'

    async def test_describe_rds_events_with_filters(self, mock_rds_client):
        """Test event retrieval with filters."""
        mock_rds_client.describe_events.return_value = {'Events': []}

        start_time = datetime(2025, 6, 1)
        end_time = datetime(2025, 6, 25)
        await describe_rds_events(
            rds_client=mock_rds_client,
            source_identifier='test-instance',
            source_type='db-instance',
            event_categories=['backup', 'recovery'],
            start_time=start_time,
            end_time=end_time,
        )

        mock_rds_client.describe_events.assert_called_once_with(
            SourceIdentifier='test-instance',
            SourceType='db-instance',
            MaxRecords=100,  # From constants.MAX_ITEMS
            EventCategories=['backup', 'recovery'],
            StartTime=start_time,
            EndTime=end_time,
        )

    async def test_describe_rds_events_with_duration(self, mock_rds_client):
        """Test event retrieval with duration."""
        # Setup mock response
        mock_rds_client.describe_events.return_value = {'Events': []}

        await describe_rds_events(
            rds_client=mock_rds_client,
            source_identifier='test-instance',
            source_type='db-instance',
            duration=60,  # 60 minutes
        )

        mock_rds_client.describe_events.assert_called_once_with(
            SourceIdentifier='test-instance',
            SourceType='db-instance',
            MaxRecords=100,  # From constants.MAX_ITEMS
            Duration=60,
        )

    async def test_describe_rds_events_error_handling(self, mock_rds_client):
        """Test error handling in describe_rds_events."""
        error = ClientError(
            error_response={
                'Error': {'Code': 'InvalidParameterValue', 'Message': 'Invalid parameter value'}
            },
            operation_name='DescribeEvents',
        )
        mock_rds_client.describe_events.side_effect = error

        with patch(
            'awslabs.rds_monitoring_mcp_server.events.handle_aws_error'
        ) as mock_handle_error:
            mock_handle_error.return_value = {
                'error': 'Error processing request',
                'error_code': 'InvalidParameterValue',
            }
            result = await describe_rds_events(
                rds_client=mock_rds_client,
                source_identifier='test-instance',
                source_type='db-instance',
            )

        mock_handle_error.assert_called_once()
        result_dict = json.loads(result)
        assert 'error' in result_dict
        assert result_dict['error'] == 'Error processing request'
        assert result_dict['error_code'] == 'InvalidParameterValue'
