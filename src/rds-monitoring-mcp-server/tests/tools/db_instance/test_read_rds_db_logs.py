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

"""Tests for read_rds_db_logs tool."""

import json
import pytest
from awslabs.rds_monitoring_mcp_server.tools.db_instance.read_rds_db_logs import (
    preprocess_log_content,
    read_rds_db_logs,
)


class TestPreprocessLogContent:
    """Tests for the preprocess_log_content helper function."""

    def test_preprocess_log_content_no_pattern(self):
        """Test preprocessing log content without a pattern filter."""
        log_content = 'Line 1\nLine 2\nError: Something went wrong\nLine 4'
        result = preprocess_log_content(log_content, None)
        assert result == log_content

    def test_preprocess_log_content_with_pattern(self):
        """Test preprocessing log content with a pattern filter."""
        log_content = 'Line 1\nLine 2\nError: Something went wrong\nLine 4'
        pattern = 'Error'
        result = preprocess_log_content(log_content, pattern)
        assert result == 'Error: Something went wrong'

    def test_preprocess_log_content_with_pattern_no_matches(self):
        """Test preprocessing log content with a pattern filter that has no matches."""
        log_content = 'Line 1\nLine 2\nLine 3\nLine 4'
        pattern = 'Error'
        result = preprocess_log_content(log_content, pattern)
        assert result == ''

    def test_preprocess_log_content_empty_log(self):
        """Test preprocessing empty log content."""
        log_content = ''
        pattern = 'Error'
        result = preprocess_log_content(log_content, pattern)
        assert result == ''


class TestReadRdsDbLogs:
    """Tests for the read_rds_db_logs tool."""

    @pytest.mark.asyncio
    async def test_read_rds_db_logs_basic(self, mock_rds_client):
        """Test basic execution of the read_rds_db_logs tool."""
        test_db_instance_id = 'test-db-instance'
        test_log_file_name = 'error/postgresql.log'
        test_log_content = '2025-06-01 12:00:00 UTC [1234]: ERROR: relation users does not exist\n2025-06-01 12:01:00 UTC [1234]: LOG: database system is ready to accept connections'

        mock_rds_client.download_db_log_file_portion.return_value = {
            'LogFileData': test_log_content,
            'NextToken': None,
            'AdditionalDataPending': False,
        }

        result_json = await read_rds_db_logs(
            db_instance_identifier=test_db_instance_id, log_file_name=test_log_file_name
        )

        mock_rds_client.download_db_log_file_portion.assert_called_once()
        call_args, call_kwargs = mock_rds_client.download_db_log_file_portion.call_args
        assert call_kwargs['DBInstanceIdentifier'] == test_db_instance_id
        assert call_kwargs['LogFileName'] == test_log_file_name
        assert call_kwargs['NumberOfLines'] == 100
        assert call_kwargs['Marker'] == '0'

        result = json.loads(result_json)
        assert result['log_content'] == test_log_content
        assert result['next_marker'] is None
        assert result['additional_data_pending'] is False

    @pytest.mark.asyncio
    async def test_read_rds_db_logs_with_pattern(self, mock_rds_client):
        """Test read_rds_db_logs with a pattern filter."""
        test_db_instance_id = 'test-db-instance'
        test_log_file_name = 'error/postgresql.log'
        test_log_content = '2025-06-01 12:00:00 UTC [1234]: ERROR: relation users does not exist\n2025-06-01 12:01:00 UTC [1234]: LOG: database system is ready to accept connections'
        pattern = 'ERROR'

        mock_rds_client.download_db_log_file_portion.return_value = {
            'LogFileData': test_log_content,
            'NextToken': None,
            'AdditionalDataPending': False,
        }

        result_json = await read_rds_db_logs(
            db_instance_identifier=test_db_instance_id,
            log_file_name=test_log_file_name,
            pattern=pattern,
        )

        result = json.loads(result_json)
        assert 'ERROR: relation users does not exist' in result['log_content']
        assert 'LOG: database system is ready' not in result['log_content']

    @pytest.mark.asyncio
    async def test_read_rds_db_logs_with_pagination(self, mock_rds_client):
        """Test read_rds_db_logs with pagination markers."""
        test_db_instance_id = 'test-db-instance'
        test_log_file_name = 'error/postgresql.log'
        test_log_content = 'First part of the log content'
        test_next_marker = '1000'

        mock_rds_client.download_db_log_file_portion.return_value = {
            'LogFileData': test_log_content,
            'NextToken': test_next_marker,
            'AdditionalDataPending': True,
        }

        result_json = await read_rds_db_logs(
            db_instance_identifier=test_db_instance_id,
            log_file_name=test_log_file_name,
            marker='500',  # Custom starting marker
        )

        mock_rds_client.download_db_log_file_portion.assert_called_once()
        call_args, call_kwargs = mock_rds_client.download_db_log_file_portion.call_args
        assert call_kwargs['DBInstanceIdentifier'] == test_db_instance_id
        assert call_kwargs['LogFileName'] == test_log_file_name
        assert call_kwargs['NumberOfLines'] == 100
        assert call_kwargs['Marker'] == '500'

        result = json.loads(result_json)
        assert result['log_content'] == test_log_content
        assert result['next_marker'] == test_next_marker
        assert result['additional_data_pending'] is True

    @pytest.mark.asyncio
    async def test_read_rds_db_logs_custom_line_count(self, mock_rds_client):
        """Test read_rds_db_logs with custom number of lines."""
        test_db_instance_id = 'test-db-instance'
        test_log_file_name = 'error/postgresql.log'
        custom_line_count = 50

        mock_rds_client.download_db_log_file_portion.return_value = {
            'LogFileData': 'Log content',
            'NextToken': None,
            'AdditionalDataPending': False,
        }

        await read_rds_db_logs(
            db_instance_identifier=test_db_instance_id,
            log_file_name=test_log_file_name,
            number_of_lines=custom_line_count,
        )

        mock_rds_client.download_db_log_file_portion.assert_called_once()
        call_args, call_kwargs = mock_rds_client.download_db_log_file_portion.call_args
        assert call_kwargs['DBInstanceIdentifier'] == test_db_instance_id
        assert call_kwargs['LogFileName'] == test_log_file_name
        assert call_kwargs['NumberOfLines'] == custom_line_count
        assert call_kwargs['Marker'] == '0'

    @pytest.mark.asyncio
    async def test_read_rds_db_logs_empty_response(self, mock_rds_client):
        """Test read_rds_db_logs when the API returns an empty response."""
        test_db_instance_id = 'test-db-instance'
        test_log_file_name = 'error/postgresql.log'

        mock_rds_client.download_db_log_file_portion.return_value = {
            'LogFileData': '',
            'NextToken': None,
            'AdditionalDataPending': False,
        }

        result_json = await read_rds_db_logs(
            db_instance_identifier=test_db_instance_id, log_file_name=test_log_file_name
        )

        result = json.loads(result_json)
        assert result['log_content'] == ''
        assert result['next_marker'] is None
        assert result['additional_data_pending'] is False
