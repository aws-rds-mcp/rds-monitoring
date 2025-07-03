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

"""Tests for RDS DB log files listing functionality."""

import pytest
from awslabs.rds_monitoring_mcp_server.resources.db_instance.list_db_logs import (
    DBLogFileListModel,
    list_db_log_files,
)
from datetime import datetime
from unittest.mock import MagicMock, patch


class TestListDBLogFiles:
    """Tests for the list_db_log_files MCP resource."""

    @pytest.mark.asyncio
    async def test_standard_response(self, mock_rds_client):
        """Test with standard response containing log files."""
        mock_log_files = [
            {
                'LogFileName': 'error/mysql-error.log',
                'LastWritten': 1625097600000,
                'Size': 1024,
            },
            {
                'LogFileName': 'error/mysql-error-previous.log',
                'LastWritten': 1624838400000,
                'Size': 2048,
            },
        ]

        mock_paginator = MagicMock()
        mock_paginator_iterator = MagicMock()

        mock_rds_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = mock_paginator_iterator
        mock_paginator_iterator.__iter__.return_value = [{'DescribeDBLogFiles': mock_log_files}]

        result = await list_db_log_files('test-instance')

        mock_rds_client.get_paginator.assert_called_once_with('describe_db_log_files')
        mock_paginator.paginate.assert_called_once()

        call_args = mock_paginator.paginate.call_args[1]
        assert call_args['DBInstanceIdentifier'] == 'test-instance'
        assert call_args['FileSize'] == 1

        assert isinstance(result, DBLogFileListModel)
        assert result.count == 2
        assert len(result.log_files) == 2

        assert result.log_files[0].log_file_name == 'error/mysql-error.log'
        assert result.log_files[0].size == 1024
        assert result.log_files[0].last_written == datetime.fromtimestamp(1625097600000 / 1000)

        assert result.log_files[1].log_file_name == 'error/mysql-error-previous.log'
        assert result.log_files[1].size == 2048
        assert result.log_files[1].last_written == datetime.fromtimestamp(1624838400000 / 1000)

    @pytest.mark.asyncio
    async def test_empty_response(self, mock_rds_client):
        """Test with empty response containing no log files."""
        mock_paginator = MagicMock()
        mock_paginator_iterator = MagicMock()

        mock_rds_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = mock_paginator_iterator
        mock_paginator_iterator.__iter__.return_value = [{'DescribeDBLogFiles': []}]

        result = await list_db_log_files('test-instance')

        assert isinstance(result, DBLogFileListModel)
        assert result.count == 0
        assert len(result.log_files) == 0

    @pytest.mark.asyncio
    async def test_multiple_pages(self, mock_rds_client):
        """Test with multiple pages of log files."""
        mock_log_files_page1 = [
            {
                'LogFileName': 'error/mysql-error.log',
                'LastWritten': 1625097600000,
                'Size': 1024,
            },
        ]

        mock_log_files_page2 = [
            {
                'LogFileName': 'error/mysql-error-previous.log',
                'LastWritten': 1624838400000,
                'Size': 2048,
            },
        ]

        mock_paginator = MagicMock()
        mock_paginator_iterator = MagicMock()

        mock_rds_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = mock_paginator_iterator
        mock_paginator_iterator.__iter__.return_value = [
            {'DescribeDBLogFiles': mock_log_files_page1},
            {'DescribeDBLogFiles': mock_log_files_page2},
        ]

        result = await list_db_log_files('test-instance')

        assert isinstance(result, DBLogFileListModel)
        assert result.count == 2
        assert len(result.log_files) == 2

        assert result.log_files[0].log_file_name == 'error/mysql-error.log'
        assert result.log_files[1].log_file_name == 'error/mysql-error-previous.log'

    @pytest.mark.asyncio
    async def test_missing_fields(self, mock_rds_client):
        """Test handling of missing fields in AWS response."""
        mock_log_files = [
            {
                'LogFileName': 'error/mysql-error.log',
                'Size': 1024,
            },
            {
                'LastWritten': 1624838400000,
                'Size': 2048,
            },
            {
                'LogFileName': 'error/mysql-slow-query.log',
                'LastWritten': 1624838400000,
            },
        ]

        mock_paginator = MagicMock()
        mock_paginator_iterator = MagicMock()

        mock_rds_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = mock_paginator_iterator
        mock_paginator_iterator.__iter__.return_value = [{'DescribeDBLogFiles': mock_log_files}]

        result = await list_db_log_files('test-instance')

        assert isinstance(result, DBLogFileListModel)
        assert result.count == 3
        assert len(result.log_files) == 3

        assert result.log_files[0].log_file_name == 'error/mysql-error.log'
        assert result.log_files[0].last_written == datetime.fromtimestamp(0)

        assert result.log_files[1].log_file_name == ''
        assert result.log_files[1].last_written == datetime.fromtimestamp(1624838400000 / 1000)

        assert result.log_files[2].log_file_name == 'error/mysql-slow-query.log'
        assert result.log_files[2].size == 0

    @pytest.mark.asyncio
    @patch('awslabs.rds_monitoring_mcp_server.resources.db_instance.list_db_logs.Context')
    async def test_pagination_config(self, mock_context, mock_rds_client):
        """Test that pagination configuration is properly set."""
        mock_pagination_config = {'MaxItems': 50, 'PageSize': 10}
        mock_context.get_pagination_config.return_value = mock_pagination_config

        mock_paginator = MagicMock()
        mock_paginator_iterator = MagicMock()

        mock_rds_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = mock_paginator_iterator
        mock_paginator_iterator.__iter__.return_value = [{'DescribeDBLogFiles': []}]

        await list_db_log_files('test-instance')

        mock_context.get_pagination_config.assert_called_once()
        mock_paginator.paginate.assert_called_once()

        call_args = mock_paginator.paginate.call_args[1]
        assert call_args['PaginationConfig'] == mock_pagination_config
