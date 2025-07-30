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

"""Tests for RDS performance reports listing functionality."""

import pytest
from awslabs.rds_monitoring_mcp_server.resources.db_instance.list_performance_reports import (
    PerformanceReportList,
    list_performance_reports,
)
from datetime import datetime


class TestListPerformanceReports:
    """Tests for the list_performance_reports MCP resource."""

    @pytest.mark.asyncio
    async def test_standard_response(self, mock_context, mock_pi_client):
        """Test with standard response containing performance reports."""
        mock_create_time = datetime(2023, 1, 1, 0, 0, 0)
        mock_start_time = datetime(2023, 1, 1, 1, 0, 0)
        mock_end_time = datetime(2023, 1, 1, 2, 0, 0)

        mock_reports = [
            {
                'AnalysisReportId': 'report-1',
                'CreateTime': mock_create_time,
                'StartTime': mock_start_time,
                'EndTime': mock_end_time,
                'Status': 'SUCCEEDED',
            },
            {
                'AnalysisReportId': 'report-2',
                'CreateTime': mock_create_time,
                'StartTime': mock_start_time,
                'EndTime': mock_end_time,
                'Status': 'RUNNING',
            },
        ]

        mock_pi_client.list_performance_analysis_reports.return_value = {
            'AnalysisReports': mock_reports
        }

        result = await list_performance_reports('db-instance-123')

        mock_pi_client.list_performance_analysis_reports.assert_called_once_with(
            ServiceType='RDS', Identifier='db-instance-123'
        )

        assert isinstance(result, PerformanceReportList)
        assert result.count == 2
        assert len(result.reports) == 2

        assert result.reports[0].analysis_report_id == 'report-1'
        assert result.reports[0].status == 'SUCCEEDED'

        assert result.reports[1].analysis_report_id == 'report-2'
        assert result.reports[1].status == 'RUNNING'

    @pytest.mark.asyncio
    async def test_empty_response(self, mock_context, mock_pi_client):
        """Test with empty response containing no performance reports."""
        mock_pi_client.list_performance_analysis_reports.return_value = {'AnalysisReports': []}

        result = await list_performance_reports('db-instance-123')

        assert isinstance(result, PerformanceReportList)
        assert result.count == 0
        assert len(result.reports) == 0

    @pytest.mark.asyncio
    async def test_missing_fields(self, mock_context, mock_pi_client):
        """Test handling of missing fields in AWS response."""
        mock_create_time = datetime(2023, 1, 1, 0, 0, 0)

        mock_reports = [
            {
                'AnalysisReportId': 'report-1',
                'StartTime': mock_create_time,
                'EndTime': mock_create_time,
                'Status': 'SUCCEEDED',
            },
            {
                # Missing AnalysisReportId
                'CreateTime': mock_create_time,
                'StartTime': mock_create_time,
                'EndTime': mock_create_time,
                # Missing Status
            },
            {
                'AnalysisReportId': 'report-3',
                'CreateTime': None,
                'StartTime': None,
                'EndTime': None,
                'Status': 'FAILED',
            },
        ]

        mock_pi_client.list_performance_analysis_reports.return_value = {
            'AnalysisReports': mock_reports
        }

        result = await list_performance_reports('db-instance-123')

        assert isinstance(result, PerformanceReportList)
        assert result.count == 3
        assert len(result.reports) == 3

        assert result.reports[0].analysis_report_id == 'report-1'
        assert result.reports[0].create_time is None
        assert result.reports[0].status == 'SUCCEEDED'

        assert result.reports[1].analysis_report_id is None
        assert result.reports[1].status is None

        assert result.reports[2].analysis_report_id == 'report-3'
        assert result.reports[2].create_time is None
        assert result.reports[2].start_time is None
        assert result.reports[2].end_time is None
        assert result.reports[2].status == 'FAILED'
