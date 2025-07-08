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
from unittest.mock import patch


class TestReadPerformanceReport:
    """Tests for the read_performance_report MCP resource."""

    @pytest.fixture
    def mock_timestamps(self):
        """Common timestamp fixture for tests."""
        return {
            'create_time': datetime(2023, 1, 1, 0, 0, 0),
            'start_time': datetime(2023, 1, 1, 1, 0, 0),
            'end_time': datetime(2023, 1, 1, 2, 0, 0),
        }

    @pytest.mark.asyncio
    async def test_standard_response(self, mock_pi_client, mock_timestamps):
        """Test with standard response containing a complete performance report."""
        # Setup test data
        test_dbi_resource_id = 'db-instance-123'
        test_report_id = 'report-1'

        mock_report = {
            'AnalysisReportId': test_report_id,
            'Identifier': test_dbi_resource_id,
            'ServiceType': 'RDS',
            'CreateTime': mock_timestamps['create_time'],
            'StartTime': mock_timestamps['start_time'],
            'EndTime': mock_timestamps['end_time'],
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

        result = await read_performance_report(test_dbi_resource_id, test_report_id)

        mock_pi_client.get_performance_analysis_report.assert_called_once_with(
            ServiceType='RDS',
            Identifier=test_dbi_resource_id,
            AnalysisReportId=test_report_id,
            TextFormat='MARKDOWN',
        )

        assert isinstance(result, AnalysisReport)
        assert result.AnalysisReportId == test_report_id
        assert result.Identifier == test_dbi_resource_id
        assert result.ServiceType == 'RDS'
        assert result.CreateTime == mock_timestamps['create_time']
        assert result.StartTime == mock_timestamps['start_time']
        assert result.EndTime == mock_timestamps['end_time']
        assert result.Status == 'SUCCEEDED'
        assert len(result.Insights) == 2
        assert result.Insights[0]['InsightType'] == 'PERFORMANCE_ANOMALY'
        assert result.Insights[0]['Impact'] == 'HIGH'
        assert result.Insights[1]['InsightType'] == 'QUERY_ANALYSIS'
        assert result.Insights[1]['Impact'] == 'MEDIUM'

    @pytest.mark.asyncio
    async def test_running_status(self, mock_pi_client, mock_timestamps):
        """Test with a report in RUNNING status (partial results)."""
        test_dbi_resource_id = 'db-instance-123'
        test_report_id = 'report-2'

        mock_report = {
            'AnalysisReportId': test_report_id,
            'Identifier': test_dbi_resource_id,
            'ServiceType': 'RDS',
            'CreateTime': mock_timestamps['create_time'],
            'StartTime': mock_timestamps['start_time'],
            'EndTime': mock_timestamps['end_time'],
            'Status': 'RUNNING',
            'Insights': [],
        }

        mock_pi_client.get_performance_analysis_report.return_value = {
            'AnalysisReport': mock_report
        }

        result = await read_performance_report(test_dbi_resource_id, test_report_id)

        mock_pi_client.get_performance_analysis_report.assert_called_once_with(
            ServiceType='RDS',
            Identifier=test_dbi_resource_id,
            AnalysisReportId=test_report_id,
            TextFormat='MARKDOWN',
        )

        assert isinstance(result, AnalysisReport)
        assert result.AnalysisReportId == test_report_id
        assert result.Identifier == test_dbi_resource_id
        assert result.ServiceType == 'RDS'
        assert result.Status == 'RUNNING'
        assert result.CreateTime == mock_timestamps['create_time']
        assert result.StartTime == mock_timestamps['start_time']
        assert result.EndTime == mock_timestamps['end_time']
        assert len(result.Insights) == 0

    @pytest.mark.asyncio
    async def test_failed_status(self, mock_pi_client, mock_timestamps):
        """Test with a report in FAILED status (with error information)."""
        test_dbi_resource_id = 'db-instance-123'
        test_report_id = 'report-3'

        mock_report = {
            'AnalysisReportId': test_report_id,
            'Identifier': test_dbi_resource_id,
            'ServiceType': 'RDS',
            'CreateTime': mock_timestamps['create_time'],
            'StartTime': mock_timestamps['start_time'],
            'EndTime': mock_timestamps['end_time'],
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

        result = await read_performance_report(test_dbi_resource_id, test_report_id)

        mock_pi_client.get_performance_analysis_report.assert_called_once_with(
            ServiceType='RDS',
            Identifier=test_dbi_resource_id,
            AnalysisReportId=test_report_id,
            TextFormat='MARKDOWN',
        )

        assert isinstance(result, AnalysisReport)
        assert result.AnalysisReportId == test_report_id
        assert result.Identifier == test_dbi_resource_id
        assert result.ServiceType == 'RDS'
        assert result.Status == 'FAILED'
        assert result.CreateTime == mock_timestamps['create_time']
        assert result.StartTime == mock_timestamps['start_time']
        assert result.EndTime == mock_timestamps['end_time']
        assert len(result.Insights) == 1
        assert result.Insights[0]['InsightType'] == 'ERROR'
        assert 'insufficient data' in result.Insights[0]['Description']

    @pytest.mark.asyncio
    async def test_empty_report(self, mock_pi_client, mock_timestamps):
        """Test with an empty analysis report."""
        test_dbi_resource_id = 'db-instance-123'
        test_report_id = 'empty-report'

        mock_report = {
            'AnalysisReportId': '',
            'Identifier': '',
            'ServiceType': '',
            'CreateTime': mock_timestamps['create_time'],
            'StartTime': mock_timestamps['start_time'],
            'EndTime': mock_timestamps['end_time'],
            'Status': '',
        }

        mock_pi_client.get_performance_analysis_report.return_value = {
            'AnalysisReport': mock_report
        }

        result = await read_performance_report(test_dbi_resource_id, test_report_id)

        mock_pi_client.get_performance_analysis_report.assert_called_once_with(
            ServiceType='RDS',
            Identifier=test_dbi_resource_id,
            AnalysisReportId=test_report_id,
            TextFormat='MARKDOWN',
        )

        assert isinstance(result, AnalysisReport)
        assert result.AnalysisReportId == ''
        assert result.Identifier == ''
        assert result.ServiceType == ''
        assert result.Status == ''
        assert result.CreateTime == mock_timestamps['create_time']
        assert result.StartTime == mock_timestamps['start_time']
        assert result.EndTime == mock_timestamps['end_time']
        assert not hasattr(result, 'Insights') or len(result.Insights) == 0

    @pytest.mark.asyncio
    async def test_report_with_missing_fields(self, mock_pi_client, mock_timestamps):
        """Test handling of reports with missing optional fields."""
        test_dbi_resource_id = 'db-instance-123'
        test_report_id = 'minimal-report'

        mock_report = {
            'AnalysisReportId': test_report_id,
            'Identifier': test_dbi_resource_id,
            'ServiceType': 'RDS',
            'CreateTime': mock_timestamps['create_time'],
            'StartTime': mock_timestamps['start_time'],
            'EndTime': mock_timestamps['end_time'],
            'Status': 'SUCCEEDED',
        }

        mock_pi_client.get_performance_analysis_report.return_value = {
            'AnalysisReport': mock_report
        }

        result = await read_performance_report(test_dbi_resource_id, test_report_id)

        assert isinstance(result, AnalysisReport)
        assert result.AnalysisReportId == test_report_id
        assert result.Identifier == test_dbi_resource_id
        assert result.Status == 'SUCCEEDED'
        assert len(result.Insights) == 0  # Should have empty list as default

    @pytest.mark.asyncio
    async def test_model_validate_behavior(self, mock_pi_client, mock_timestamps):
        """Test that model_validate is used for creating the AnalysisReport."""
        test_dbi_resource_id = 'db-instance-123'
        test_report_id = 'model-validate-test'

        mock_report = {
            'AnalysisReportId': test_report_id,
            'Identifier': test_dbi_resource_id,
            'ServiceType': 'RDS',
            'CreateTime': mock_timestamps['create_time'],
            'StartTime': mock_timestamps['start_time'],
            'EndTime': mock_timestamps['end_time'],
            'Status': 'SUCCEEDED',
            'Insights': [
                {'InsightType': 'TEST_INSIGHT', 'Description': 'Test insight description'}
            ],
        }

        mock_pi_client.get_performance_analysis_report.return_value = {
            'AnalysisReport': mock_report
        }

        with patch.object(
            AnalysisReport, 'model_validate', wraps=AnalysisReport.model_validate
        ) as mock_validate:
            result = await read_performance_report(test_dbi_resource_id, test_report_id)

            mock_validate.assert_called_once_with(mock_report)

            assert isinstance(result, AnalysisReport)
            assert result.AnalysisReportId == test_report_id
            assert result.Identifier == test_dbi_resource_id
            assert result.ServiceType == 'RDS'
            assert len(result.Insights) == 1
            assert result.Insights[0]['InsightType'] == 'TEST_INSIGHT'
