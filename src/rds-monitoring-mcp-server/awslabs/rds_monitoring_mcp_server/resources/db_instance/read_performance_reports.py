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

"""aws-rds://db-instance/{dbi_resource_identifier}/performance_report/{report_id} resource implementation."""

from ...common.connection import PIConnectionManager
from ...common.decorators.handle_exceptions import handle_exceptions
from ...common.decorators.register_mcp_primitive import register_mcp_primitive_by_context
from datetime import datetime
from loguru import logger
from pydantic import BaseModel, Field
from typing import Any, Dict, List


RESOURCE_DESCRIPTION = """Read the contents of a specific performance report for a specific Amazon RDS instance.

<important_notes>
1. You must provide both a valid dbi_resource_identifier and report identifier
2. The report must be in a SUCCEEDED status to be fully readable
</important_notes>
"""


class AnalysisReport(BaseModel):
    """Model representing a complete performance analysis report."""

    AnalysisReportId: str
    Identifier: str
    ServiceType: str
    CreateTime: datetime
    StartTime: datetime
    EndTime: datetime
    Status: str
    Insights: List[Dict[str, Any]] = []


resource_params = {
    'uri': 'aws-rds://db-instance/{dbi_resource_identifier}/performance_report/{report_id}',
    'name': 'ReadPerformanceReport',
    'mime_type': 'application/json',
    'description': RESOURCE_DESCRIPTION,
}

tool_params = {
    'name': 'ReadPerformanceReport',
    'description': RESOURCE_DESCRIPTION,
}


@register_mcp_primitive_by_context(resource_params, tool_params)
@handle_exceptions
async def read_performance_report(
    dbi_resource_identifier: str = Field(
        ...,
        description='The AWS Region-unique, immutable identifier for the DB instance. This is the DbiResourceId returned by the ListDBInstances resource',
    ),
    report_id: str = Field(
        ..., description='The unique identifier of the performance analysis report to retrieve'
    ),
) -> AnalysisReport:
    """Retrieve a specific performance report from AWS Performance Insights.

    Args:
        dbi_resource_identifier: The resource identifier for the DB instance
        report_id: The ID of the performance report to read

    Returns:
        JSON string containing the complete performance report data including metrics, analysis, and recommendations
    """
    logger.info(
        f'Retrieving performance report {report_id} for DB instance {dbi_resource_identifier}'
    )
    pi_client = PIConnectionManager.get_connection()

    response = pi_client.get_performance_analysis_report(
        ServiceType='RDS',
        Identifier=dbi_resource_identifier,
        AnalysisReportId=report_id,
        TextFormat='MARKDOWN',
    )

    analysis_report = response.get('AnalysisReport', {})
    return AnalysisReport.model_validate(analysis_report)
