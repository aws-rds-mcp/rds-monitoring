"""Tests for the describe_rds_events module."""

import pytest
from awslabs.rds_monitoring_mcp_server.tools.general.describe_rds_events import (
    Event,
    EventList,
    describe_rds_events,
)
from datetime import datetime, timezone


def create_test_event():
    """Create a sample event for testing."""
    return {
        'Message': 'Test event message',
        'EventCategories': ['backup', 'recovery'],
        'Date': datetime(2025, 1, 1, tzinfo=timezone.utc),
        'SourceArn': 'arn:aws:rds:us-west-2:123456789012:db:test-instance',
    }


class TestEvent:
    """Tests for the Event model."""

    def test_from_event_data(self):
        """Test the Event.from_event_data method."""
        event = create_test_event()
        formatted_event = Event.from_event_data(event)

        assert isinstance(formatted_event, Event)
        assert formatted_event.message == 'Test event message'
        assert formatted_event.event_categories == ['backup', 'recovery']
        assert formatted_event.date == '2025-01-01T00:00:00+00:00'
        assert formatted_event.source_arn == 'arn:aws:rds:us-west-2:123456789012:db:test-instance'

    def test_from_event_data_no_date(self):
        """Test Event.from_event_data with no date."""
        event_no_date = create_test_event()
        event_no_date['Date'] = None
        formatted_event = Event.from_event_data(event_no_date)

        assert formatted_event.date == ''

    def test_from_event_data_string_date(self):
        """Test Event.from_event_data with string date."""
        event_string_date = create_test_event()
        event_string_date['Date'] = '2025-01-01'
        formatted_event = Event.from_event_data(event_string_date)

        assert formatted_event.date == '2025-01-01'

    def test_from_event_data_minimal(self):
        """Test Event.from_event_data with minimal data."""
        event_minimal = {}
        formatted_event = Event.from_event_data(event_minimal)

        assert formatted_event.message == ''
        assert formatted_event.event_categories == []
        assert formatted_event.date == ''
        assert formatted_event.source_arn is None


class TestDescribeRDSEvents:
    """Tests for the describe_rds_events function."""

    @pytest.mark.asyncio
    async def test_describe_rds_events_basic(self, mock_rds_client, mock_context):
        """Test the describe_rds_events function with basic parameters."""
        mock_rds_client.describe_events.return_value = {'Events': [create_test_event()]}

        result = await describe_rds_events(
            source_identifier='test-db-instance',
            source_type='db-instance',
        )

        mock_rds_client.describe_events.assert_called_once()
        call_kwargs = mock_rds_client.describe_events.call_args[1]
        assert call_kwargs['SourceIdentifier'] == 'test-db-instance'
        assert call_kwargs['SourceType'] == 'db-instance'

        assert isinstance(result, EventList)
        assert result.source_identifier == 'test-db-instance'
        assert result.source_type == 'db-instance'
        assert result.count == 1
        assert len(result.events) == 1

        event = result.events[0]
        assert event.message == 'Test event message'
        assert event.event_categories == ['backup', 'recovery']
        assert event.source_arn == 'arn:aws:rds:us-west-2:123456789012:db:test-instance'

    @pytest.mark.asyncio
    async def test_describe_rds_events_with_filters(self, mock_rds_client, mock_context):
        """Test the describe_rds_events function with various filters."""
        mock_rds_client.describe_events.return_value = {'Events': [create_test_event()]}

        result = await describe_rds_events(
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
        assert isinstance(result, EventList)

    @pytest.mark.asyncio
    async def test_describe_rds_events_no_events(self, mock_rds_client, mock_context):
        """Test the describe_rds_events function when no events are found."""
        mock_rds_client.describe_events.return_value = {'Events': []}

        result = await describe_rds_events(
            source_identifier='test-db-instance',
            source_type='db-instance',
        )

        assert isinstance(result, EventList)
        assert result.count == 0
        assert len(result.events) == 0

    @pytest.mark.asyncio
    async def test_describe_rds_events_different_source_types(self, mock_rds_client, mock_context):
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
            result = await describe_rds_events(
                source_identifier=f'test-{source_type}',
                source_type=source_type,
            )

            assert mock_rds_client.describe_events.call_args[1]['SourceType'] == source_type
            assert isinstance(result, EventList)
            assert result.source_type == source_type
            mock_rds_client.reset_mock()
