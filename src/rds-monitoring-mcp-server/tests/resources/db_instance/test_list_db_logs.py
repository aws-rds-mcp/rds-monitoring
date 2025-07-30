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

"""Tests for list_db_log_files resource."""

import pytest
from awslabs.rds_monitoring_mcp_server.resources.db_instance.list_db_logs import (
    DBLogFileSummary,
    list_db_log_files,
)
from datetime import datetime
from unittest.mock import patch


class TestListDBLogFiles:
    """Test list_db_log_files function."""

    @pytest.mark.asyncio
    async def test_success(self, mock_rds_client):
        """Test successful log file retrieval."""
        mock_log_file = DBLogFileSummary(
            log_file_name='error/mysql-error.log',
            last_written=datetime(2024, 1, 1, 12, 0, 0),
            size=1024,
        )

        with patch(
            'awslabs.rds_monitoring_mcp_server.resources.db_instance.list_db_logs.handle_paginated_aws_api_call'
        ) as mock_call:
            mock_call.return_value = [mock_log_file]

            result = await list_db_log_files(db_instance_identifier='test-instance')

        assert result.count == 1
        assert len(result.log_files) == 1
        assert result.log_files[0].log_file_name == 'error/mysql-error.log'

    @pytest.mark.asyncio
    async def test_empty_response(self, mock_rds_client):
        """Test handling of empty log file response."""
        with patch(
            'awslabs.rds_monitoring_mcp_server.resources.db_instance.list_db_logs.handle_paginated_aws_api_call'
        ) as mock_call:
            mock_call.return_value = []

            result = await list_db_log_files(db_instance_identifier='test-instance')

        assert result.count == 0
        assert len(result.log_files) == 0


class TestDBLogFileSummary:
    """Test DBLogFileSummary model."""

    def test_model_creation(self):
        """Test model creation with valid data."""
        log_file = DBLogFileSummary(
            log_file_name='error/mysql-error.log',
            last_written=datetime(2024, 1, 1, 12, 0, 0),
            size=2048,
        )

        assert log_file.log_file_name == 'error/mysql-error.log'
        assert log_file.last_written == datetime(2024, 1, 1, 12, 0, 0)
        assert log_file.size == 2048
