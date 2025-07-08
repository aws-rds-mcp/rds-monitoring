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

"""Tests for create_performance_report tool."""

import pytest
from awslabs.rds_monitoring_mcp_server.tools.db_instance.create_performance_report import (
    REPORT_CREATION_SUCCESS_RESPONSE,
    create_performance_report,
)
from datetime import datetime
from unittest.mock import patch


class TestCreatePerformanceReport:
    """Tests for the create_performance_report tool."""

    @pytest.mark.asyncio
    async def test_create_performance_report_success(self, mock_pi_client):
        """Test successful performance report creation."""
        # Arrange
        test_dbi_resource_id = 'db-ABCDEFGHIJKLMNO123456'
        test_report_id = 'pi-report-123456789'

        mock_pi_client.create_performance_analysis_report.return_value = {
            'AnalysisReportId': test_report_id
        }

        # Act
        with patch(
            'awslabs.rds_monitoring_mcp_server.context.Context.readonly_mode', return_value=False
        ):
            result = await create_performance_report(
                dbi_resource_identifier=test_dbi_resource_id,
                start_time='2025-06-01T00:00:00Z',
                end_time='2025-06-02T00:00:00Z',
            )

        # Assert
        mock_pi_client.create_performance_analysis_report.assert_called_once()
        assert test_report_id in result
        assert test_dbi_resource_id in result
        expected_response = REPORT_CREATION_SUCCESS_RESPONSE.format(
            test_report_id, test_dbi_resource_id
        )
        assert result == expected_response

    @pytest.mark.asyncio
    async def test_create_performance_report_with_default_times(self, mock_pi_client):
        """Test performance report creation with default start and end times."""
        # Arrange
        test_dbi_resource_id = 'db-ABCDEFGHIJKLMNO123456'
        test_report_id = 'pi-report-123456789'

        mock_pi_client.create_performance_analysis_report.return_value = {
            'AnalysisReportId': test_report_id
        }

        # Act
        with (
            patch(
                'awslabs.rds_monitoring_mcp_server.context.Context.readonly_mode',
                return_value=False,
            ),
            patch('awslabs.rds_monitoring_mcp_server.common.utils.datetime') as mock_datetime,
        ):
            # Mock the datetime.now() call
            mock_now = datetime(2025, 6, 1, 12, 0, 0)
            mock_datetime.now.return_value = mock_now

            result = await create_performance_report(dbi_resource_identifier=test_dbi_resource_id)

        # Assert
        mock_pi_client.create_performance_analysis_report.assert_called_once()
        assert test_report_id in result

    @pytest.mark.asyncio
    async def test_create_performance_report_with_tags(self, mock_pi_client):
        """Test performance report creation with custom tags."""
        # Arrange
        test_dbi_resource_id = 'db-ABCDEFGHIJKLMNO123456'
        test_report_id = 'pi-report-123456789'
        test_tags = [{'Environment': 'Production'}, {'Project': 'RDS-Monitoring'}]

        mock_pi_client.create_performance_analysis_report.return_value = {
            'AnalysisReportId': test_report_id
        }

        # Act
        with patch(
            'awslabs.rds_monitoring_mcp_server.context.Context.readonly_mode', return_value=False
        ):
            result = await create_performance_report(
                dbi_resource_identifier=test_dbi_resource_id,
                start_time='2025-06-01T00:00:00Z',
                end_time='2025-06-02T00:00:00Z',
                tags=test_tags,
            )

        # Assert
        mock_pi_client.create_performance_analysis_report.assert_called_once()

        # Verify the tags were properly formatted and included
        call_kwargs = mock_pi_client.create_performance_analysis_report.call_args.kwargs
        assert 'Tags' in call_kwargs

        # Should include the MCP_SERVER_TAG plus our custom tags
        tags_passed = call_kwargs['Tags']
        assert len(tags_passed) >= 3  # At least 1 default + 2 custom tags

        # Check that our custom tags were included
        custom_tags_found = 0
        for tag in tags_passed:
            if isinstance(tag, dict) and 'Key' in tag and 'Value' in tag:
                if (tag['Key'] == 'Environment' and tag['Value'] == 'Production') or (
                    tag['Key'] == 'Project' and tag['Value'] == 'RDS-Monitoring'
                ):
                    custom_tags_found += 1

        assert custom_tags_found == 2
        assert test_report_id in result

    @pytest.mark.asyncio
    async def test_create_performance_report_readonly_mode(self, mock_pi_client):
        """Test performance report creation fails in readonly mode."""
        test_dbi_resource_id = 'db-ABCDEFGHIJKLMNO123456'

        with patch(
            'awslabs.rds_monitoring_mcp_server.context.Context.readonly_mode', return_value=True
        ):
            try:
                await create_performance_report(
                    dbi_resource_identifier=test_dbi_resource_id,
                    start_time='2025-06-01T00:00:00Z',
                    end_time='2025-06-02T00:00:00Z',
                )
            except ValueError:
                pytest.fail(
                    'Unexpected exception: handle_exceptions should have caught the ValueError'
                )

        mock_pi_client.create_performance_analysis_report.assert_not_called()
