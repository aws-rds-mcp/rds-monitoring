"""Tests for the describe_rds_events module."""

import json
import pytest
from awslabs.rds_monitoring_mcp_server.tools.general.describe_rds_events import (
    DBEvent,
    describe_rds_events,
    format_event,
)
from datetime import datetime, timezone
from mcp.server.fastmcp import Context as mcp_ctx
from unittest.mock import MagicMock


def create_test_event():
    """Create a sample event for testing."""
    return {
        'Message': 'Test event message',
        'EventCategories': ['backup', 'recovery'],
        'Date': datetime(2025, 1, 1, tzinfo=timezone.utc),
        'SourceArn': 'arn:aws:rds:us-west-2:123456789012:db:test-instance',
    }


class TestHelperFunctions:
    """Tests for helper functions in the describe_rds_events module."""

    def test_format_event(self):
        """Test the format_event function."""
        event = create_test_event()
        formatted_event = format_event(event)

        assert isinstance(formatted_event, DBEvent)
        assert formatted_event.message == 'Test event message'
        assert formatted_event.event_categories == ['backup', 'recovery']
        assert formatted_event.date == '2025-01-01T00:00:00+00:00'
        assert formatted_event.source_arn == 'arn:aws:rds:us-west-2:123456789012:db:test-instance'

        event_no_date = create_test_event()
        event_no_date['Date'] = None
        formatted_event = format_event(event_no_date)

        assert formatted_event.date == ''

        event_string_date = create_test_event()
        event_string_date['Date'] = '2025-01-01'
        formatted_event = format_event(event_string_date)

        assert formatted_event.date == '2025-01-01'

        event_minimal = {}
        formatted_event = format_event(event_minimal)

        assert formatted_event.message == ''
        assert formatted_event.event_categories == []
        assert formatted_event.date == ''
        assert formatted_event.source_arn is None


class TestDescribeRDSEvents:
    """Tests for the describe_rds_events function."""

    @pytest.mark.asyncio
    async def test_describe_rds_events_basic(self, mock_rds_client):
        """Test the describe_rds_events function with basic parameters."""
        mock_rds_client.describe_events.return_value = {'Events': [create_test_event()]}

        context = MagicMock(spec=mcp_ctx)
        result = await describe_rds_events(
            context,
            source_identifier='test-db-instance',
            source_type='db-instance',
        )

        mock_rds_client.describe_events.assert_called_once()
        call_kwargs = mock_rds_client.describe_events.call_args[1]
        assert call_kwargs['SourceIdentifier'] == 'test-db-instance'
        assert call_kwargs['SourceType'] == 'db-instance'

        result_dict = json.loads(result)
        assert result_dict['source_identifier'] == 'test-db-instance'
        assert result_dict['source_type'] == 'db-instance'
        assert result_dict['count'] == 1
        assert len(result_dict['events']) == 1

        event = result_dict['events'][0]
        assert event['message'] == 'Test event message'
        assert event['event_categories'] == ['backup', 'recovery']
        assert event['source_arn'] == 'arn:aws:rds:us-west-2:123456789012:db:test-instance'

    @pytest.mark.asyncio
    async def test_describe_rds_events_with_filters(self, mock_rds_client):
        """Test the describe_rds_events function with various filters."""
        mock_rds_client.describe_events.return_value = {'Events': [create_test_event()]}

        context = MagicMock(spec=mcp_ctx)
        await describe_rds_events(
            context,
            source_identifier='test-db-instance',
            source_type='db-instance',
            event_categories=['backup'],
            duration=60,
            start_time='2025-01-01T00:00:00Z',
            end_time='2025-01-02T00:00:00Z',
        )

        mock_rds_client.describe_events.assert_called_once()
        call_kwargs = mock_rds_client.describe_events.call_args[1]

        assert call_kwargs['SourceIdentifier'] == 'test-db-instance'
        assert call_kwargs['SourceType'] == 'db-instance'
        assert call_kwargs['EventCategories'] == ['backup']
        assert call_kwargs['Duration'] == 60
        assert call_kwargs['StartTime'] == '2025-01-01T00:00:00Z'
        assert call_kwargs['EndTime'] == '2025-01-02T00:00:00Z'

    @pytest.mark.asyncio
    async def test_describe_rds_events_no_events(self, mock_rds_client):
        """Test the describe_rds_events function when no events are found."""
        mock_rds_client.describe_events.return_value = {'Events': []}

        context = MagicMock(spec=mcp_ctx)
        result = await describe_rds_events(
            context,
            source_identifier='test-db-instance',
            source_type='db-instance',
        )

        result_dict = json.loads(result)
        assert result_dict['count'] == 0
        assert len(result_dict['events']) == 0

    @pytest.mark.asyncio
    async def test_describe_rds_events_different_source_types(self, mock_rds_client):
        """Test the describe_rds_events function with different source types."""
        mock_rds_client.describe_events.return_value = {'Events': [create_test_event()]}

        source_types = [
            'db-instance',
            'db-parameter-group',
            'db-security-group',
            'db-snapshot',
            'db-cluster',
            'db-cluster-snapshot',
        ]

        for source_type in source_types:
            context = MagicMock(spec=mcp_ctx)
            result = await describe_rds_events(
                context,
                source_identifier=f'test-{source_type}',
                source_type=source_type,
            )

            assert mock_rds_client.describe_events.call_args[1]['SourceType'] == source_type

            result_dict = json.loads(result)
            assert result_dict['source_type'] == source_type
