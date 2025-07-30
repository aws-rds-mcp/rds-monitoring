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
from unittest.mock import patch


class TestCreatePerformanceReport:
    """Tests for the create_performance_report tool."""

    @pytest.mark.asyncio
    async def test_create_performance_report_success(self, mock_pi_client):
        """Test successful performance report creation."""
        test_dbi_resource_id = 'db-ABCDEFGHIJKLMNO123456'
        test_report_id = 'pi-report-123456789'

        mock_pi_client.create_performance_analysis_report.return_value = {
            'AnalysisReportId': test_report_id
        }

        with patch(
            'awslabs.rds_monitoring_mcp_server.common.context.RDSContext.readonly_mode',
            return_value=False,
        ):
            result = await create_performance_report(
                dbi_resource_identifier=test_dbi_resource_id,
                start_time='2025-06-01T00:00:00Z',
                end_time='2025-06-02T00:00:00Z',
            )

        mock_pi_client.create_performance_analysis_report.assert_called_once()
        assert test_report_id in result
        assert test_dbi_resource_id in result
        expected_response = REPORT_CREATION_SUCCESS_RESPONSE.format(
            test_report_id, test_dbi_resource_id
        )
        assert result == expected_response

    @pytest.mark.asyncio
    async def test_create_performance_report_with_tags(self, mock_pi_client):
        """Test performance report creation includes default tags."""
        test_dbi_resource_id = 'db-ABCDEFGHIJKLMNO123456'
        test_report_id = 'pi-report-123456789'

        mock_pi_client.create_performance_analysis_report.return_value = {
            'AnalysisReportId': test_report_id
        }

        with patch(
            'awslabs.rds_monitoring_mcp_server.common.context.RDSContext.readonly_mode',
            return_value=False,
        ):
            result = await create_performance_report(
                dbi_resource_identifier=test_dbi_resource_id,
                start_time='2025-06-01T00:00:00Z',
                end_time='2025-06-02T00:00:00Z',
            )

        mock_pi_client.create_performance_analysis_report.assert_called_once()

        call_kwargs = mock_pi_client.create_performance_analysis_report.call_args.kwargs
        assert 'Tags' in call_kwargs
        tags_passed = call_kwargs['Tags']
        assert len(tags_passed) == 2

        tag_keys = [tag['Key'] for tag in tags_passed]
        assert 'mcp_server_version' in tag_keys
        assert 'created_by' in tag_keys
        assert test_report_id in result

    @pytest.mark.asyncio
    async def test_create_performance_report_readonly_mode(self, mock_pi_client):
        """Test performance report creation fails in readonly mode."""
        test_dbi_resource_id = 'db-ABCDEFGHIJKLMNO123456'

        with patch(
            'awslabs.rds_monitoring_mcp_server.common.context.RDSContext.readonly_mode',
            return_value=True,
        ):
            result = await create_performance_report(
                dbi_resource_identifier=test_dbi_resource_id,
                start_time='2025-06-01T00:00:00Z',
                end_time='2025-06-02T00:00:00Z',
            )
            assert 'error' in result.lower() or 'read-only' in result.lower()

        mock_pi_client.create_performance_analysis_report.assert_not_called()
