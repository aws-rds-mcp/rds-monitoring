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

"""Tests for read_db_log_file tool."""

import pytest
from awslabs.rds_monitoring_mcp_server.tools.db_instance.read_rds_db_file import (
    preprocess_log_content,
    read_db_log_file,
)


class TestPreprocessLogContent:
    """Tests for the preprocess_log_content helper function."""

    @pytest.mark.asyncio
    async def test_preprocess_log_content_no_pattern(self):
        """Test preprocessing log content without a pattern filter."""
        log_content = 'Line 1\nLine 2\nError: Something went wrong\nLine 4'
        result = await preprocess_log_content(log_content, None)
        assert result == log_content

    @pytest.mark.asyncio
    async def test_preprocess_log_content_with_pattern(self):
        """Test preprocessing log content with a pattern filter."""
        log_content = 'Line 1\nLine 2\nError: Something went wrong\nLine 4'
        pattern = 'Error'
        result = await preprocess_log_content(log_content, pattern)
        assert result == 'Error: Something went wrong'

    @pytest.mark.asyncio
    async def test_preprocess_log_content_with_pattern_no_matches(self):
        """Test preprocessing log content with a pattern filter that has no matches."""
        log_content = 'Line 1\nLine 2\nLine 3\nLine 4'
        pattern = 'Error'
        result = await preprocess_log_content(log_content, pattern)
        assert result == ''

    @pytest.mark.asyncio
    async def test_preprocess_log_content_empty_log(self):
        """Test preprocessing empty log content."""
        log_content = ''
        pattern = 'Error'
        result = await preprocess_log_content(log_content, pattern)
        assert result == ''


class TestReadDbLogFile:
    """Tests for the read_db_log_file tool."""

    @pytest.mark.asyncio
    async def test_read_db_log_file_basic(self, mock_rds_client, mock_context):
        """Test basic execution of the read_db_log_file tool."""
        test_db_instance_id = 'test-db-instance'
        test_log_file_name = 'error/postgresql.log'
        test_log_content = '2025-06-01 12:00:00 UTC [1234]: ERROR: relation users does not exist\n2025-06-01 12:01:00 UTC [1234]: LOG: database system is ready to accept connections'

        mock_rds_client.download_db_log_file_portion.return_value = {
            'LogFileData': test_log_content,
            'Marker': None,
            'AdditionalDataPending': False,
        }

        result = await read_db_log_file(
            db_instance_identifier=test_db_instance_id, log_file_name=test_log_file_name
        )

        mock_rds_client.download_db_log_file_portion.assert_called_once()
        call_args, call_kwargs = mock_rds_client.download_db_log_file_portion.call_args
        assert call_kwargs['DBInstanceIdentifier'] == test_db_instance_id
        assert call_kwargs['LogFileName'] == test_log_file_name
        assert call_kwargs['NumberOfLines'] == 100

        assert result.log_content == test_log_content
        assert result.next_marker is None
        assert result.additional_data_pending is False

    @pytest.mark.asyncio
    async def test_read_db_log_file_with_pattern(self, mock_rds_client, mock_context):
        """Test read_db_log_file with a pattern filter."""
        test_db_instance_id = 'test-db-instance'
        test_log_file_name = 'error/postgresql.log'
        test_log_content = '2025-06-01 12:00:00 UTC [1234]: ERROR: relation users does not exist\n2025-06-01 12:01:00 UTC [1234]: LOG: database system is ready to accept connections'
        pattern = 'ERROR'

        mock_rds_client.download_db_log_file_portion.return_value = {
            'LogFileData': test_log_content,
            'Marker': None,
            'AdditionalDataPending': False,
        }

        result = await read_db_log_file(
            db_instance_identifier=test_db_instance_id,
            log_file_name=test_log_file_name,
            pattern=pattern,
        )

        assert 'ERROR: relation users does not exist' in result.log_content
        assert 'LOG: database system is ready' not in result.log_content

    @pytest.mark.asyncio
    async def test_read_db_log_file_with_pagination(self, mock_rds_client, mock_context):
        """Test read_db_log_file with pagination markers."""
        test_db_instance_id = 'test-db-instance'
        test_log_file_name = 'error/postgresql.log'
        test_log_content = 'First part of the log content'
        test_next_marker = '1000'

        mock_rds_client.download_db_log_file_portion.return_value = {
            'LogFileData': test_log_content,
            'Marker': test_next_marker,
            'AdditionalDataPending': True,
        }

        result = await read_db_log_file(
            db_instance_identifier=test_db_instance_id,
            log_file_name=test_log_file_name,
            marker='500',
        )

        mock_rds_client.download_db_log_file_portion.assert_called_once()
        call_args, call_kwargs = mock_rds_client.download_db_log_file_portion.call_args
        assert call_kwargs['Marker'] == '500'

        assert result.log_content == test_log_content
        assert result.next_marker == test_next_marker
        assert result.additional_data_pending is True

    @pytest.mark.asyncio
    async def test_read_db_log_file_custom_line_count(self, mock_rds_client, mock_context):
        """Test read_db_log_file with custom number of lines."""
        test_db_instance_id = 'test-db-instance'
        test_log_file_name = 'error/postgresql.log'
        custom_line_count = 50

        mock_rds_client.download_db_log_file_portion.return_value = {
            'LogFileData': 'Log content',
            'Marker': None,
            'AdditionalDataPending': False,
        }

        await read_db_log_file(
            db_instance_identifier=test_db_instance_id,
            log_file_name=test_log_file_name,
            number_of_lines=custom_line_count,
        )

        mock_rds_client.download_db_log_file_portion.assert_called_once()
        call_args, call_kwargs = mock_rds_client.download_db_log_file_portion.call_args
        assert call_kwargs['NumberOfLines'] == custom_line_count

    @pytest.mark.asyncio
    async def test_read_db_log_file_empty_response(self, mock_rds_client, mock_context):
        """Test read_db_log_file when the API returns an empty response."""
        test_db_instance_id = 'test-db-instance'
        test_log_file_name = 'error/postgresql.log'

        mock_rds_client.download_db_log_file_portion.return_value = {
            'LogFileData': '',
            'Marker': None,
            'AdditionalDataPending': False,
        }

        result = await read_db_log_file(
            db_instance_identifier=test_db_instance_id, log_file_name=test_log_file_name
        )

        assert result.log_content == ''
        assert result.next_marker is None
        assert result.additional_data_pending is False
