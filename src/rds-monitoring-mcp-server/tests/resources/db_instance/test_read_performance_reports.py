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

"""Tests for RDS performance report reading functionality."""

import pytest
from awslabs.rds_monitoring_mcp_server.resources.db_instance.read_performance_reports import (
    AnalysisReport,
    read_performance_report,
)
from datetime import datetime


class TestReadPerformanceReport:
    """Tests for the read_performance_report MCP resource."""

    @pytest.mark.asyncio
    async def test_standard_response(self, mock_pi_client):
        """Test with standard response containing a complete performance report."""
        mock_create_time = datetime(2023, 1, 1, 0, 0, 0)
        mock_start_time = datetime(2023, 1, 1, 1, 0, 0)
        mock_end_time = datetime(2023, 1, 1, 2, 0, 0)

        mock_report = {
            'AnalysisReportId': 'report-1',
            'Identifier': 'db-instance-123',
            'ServiceType': 'RDS',
            'CreateTime': mock_create_time,
            'StartTime': mock_start_time,
            'EndTime': mock_end_time,
            'Status': 'SUCCEEDED',
            'Insights': [
                {
                    'InsightType': 'PERFORMANCE_ANOMALY',
                    'Description': 'High CPU utilization detected',
                    'Impact': 'HIGH',
                },
                {
                    'InsightType': 'QUERY_ANALYSIS',
                    'Description': 'Slow query detected',
                    'Impact': 'MEDIUM',
                },
            ],
        }

        mock_pi_client.get_performance_analysis_report.return_value = {
            'AnalysisReport': mock_report
        }

        result = await read_performance_report('db-instance-123', 'report-1')

        mock_pi_client.get_performance_analysis_report.assert_called_once_with(
            ServiceType='RDS',
            Identifier='db-instance-123',
            AnalysisReportId='report-1',
            TextFormat='MARKDOWN',
        )

        assert isinstance(result, AnalysisReport)
        assert result.AnalysisReportId == 'report-1'
        assert result.Identifier == 'db-instance-123'
        assert result.ServiceType == 'RDS'
        assert result.CreateTime == mock_create_time
        assert result.StartTime == mock_start_time
        assert result.EndTime == mock_end_time
        assert result.Status == 'SUCCEEDED'
        assert len(result.Insights) == 2
        assert result.Insights[0]['InsightType'] == 'PERFORMANCE_ANOMALY'
        assert result.Insights[1]['InsightType'] == 'QUERY_ANALYSIS'

    @pytest.mark.asyncio
    async def test_running_status(self, mock_pi_client):
        """Test with a report in RUNNING status (partial results)."""
        mock_create_time = datetime(2023, 1, 1, 0, 0, 0)
        mock_start_time = datetime(2023, 1, 1, 1, 0, 0)
        mock_end_time = datetime(2023, 1, 1, 2, 0, 0)

        mock_report = {
            'AnalysisReportId': 'report-2',
            'Identifier': 'db-instance-123',
            'ServiceType': 'RDS',
            'CreateTime': mock_create_time,
            'StartTime': mock_start_time,
            'EndTime': mock_end_time,
            'Status': 'RUNNING',
            'Insights': [],
        }

        mock_pi_client.get_performance_analysis_report.return_value = {
            'AnalysisReport': mock_report
        }

        result = await read_performance_report('db-instance-123', 'report-2')

        assert isinstance(result, AnalysisReport)
        assert result.AnalysisReportId == 'report-2'
        assert result.Status == 'RUNNING'
        assert len(result.Insights) == 0

    @pytest.mark.asyncio
    async def test_failed_status(self, mock_pi_client):
        """Test with a report in FAILED status (with error information)."""
        mock_create_time = datetime(2023, 1, 1, 0, 0, 0)
        mock_start_time = datetime(2023, 1, 1, 1, 0, 0)
        mock_end_time = datetime(2023, 1, 1, 2, 0, 0)

        mock_report = {
            'AnalysisReportId': 'report-3',
            'Identifier': 'db-instance-123',
            'ServiceType': 'RDS',
            'CreateTime': mock_create_time,
            'StartTime': mock_start_time,
            'EndTime': mock_end_time,
            'Status': 'FAILED',
            'Insights': [
                {
                    'InsightType': 'ERROR',
                    'Description': 'Failed to analyze performance due to insufficient data',
                }
            ],
        }

        mock_pi_client.get_performance_analysis_report.return_value = {
            'AnalysisReport': mock_report
        }

        result = await read_performance_report('db-instance-123', 'report-3')

        assert isinstance(result, AnalysisReport)
        assert result.AnalysisReportId == 'report-3'
        assert result.Status == 'FAILED'
        assert len(result.Insights) == 1
        assert result.Insights[0]['InsightType'] == 'ERROR'

    @pytest.mark.asyncio
    async def test_empty_report(self, mock_pi_client):
        """Test with an empty analysis report."""
        mock_create_time = datetime(2023, 1, 1, 0, 0, 0)
        mock_start_time = datetime(2023, 1, 1, 1, 0, 0)
        mock_end_time = datetime(2023, 1, 1, 2, 0, 0)

        mock_report = {
            'AnalysisReportId': '',
            'Identifier': '',
            'ServiceType': '',
            'CreateTime': mock_create_time,
            'StartTime': mock_start_time,
            'EndTime': mock_end_time,
            'Status': '',
        }

        mock_pi_client.get_performance_analysis_report.return_value = {
            'AnalysisReport': mock_report
        }

        result = await read_performance_report('db-instance-123', 'empty-report')

        assert isinstance(result, AnalysisReport)
        assert result.AnalysisReportId == ''
        assert result.Identifier == ''
        assert result.ServiceType == ''
        assert result.Status == ''
        assert result.CreateTime == mock_create_time
        assert result.StartTime == mock_start_time
        assert result.EndTime == mock_end_time
        assert len(result.Insights) == 0
