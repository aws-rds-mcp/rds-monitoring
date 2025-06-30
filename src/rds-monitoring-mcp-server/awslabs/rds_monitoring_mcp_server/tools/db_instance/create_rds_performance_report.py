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

"""create_rds_performance_report helpers and tool implementation."""

from ...common.connection import PIConnectionManager
from ...common.constants import MCP_SERVER_TAG
from ...common.decorators import handle_exceptions
from ...common.server import mcp
from ...common.utils import convert_string_to_datetime
from ...context import Context
from datetime import datetime, timedelta
from loguru import logger
from mcp.types import ToolAnnotations
from pydantic import Field
from typing import Dict, List, Optional


# MCP Tool Args

REPORT_CREATION_SUCCESS_RESPONSE = """Performance analysis report creation has been initiated successfully.

The report ID is: {}

This process is asynchronous and will take some time to complete. Once generated,
you can access the report details using the Performance Insights dashboard or the aws-rds://db-instance/{}/performance_report resource.

Note: Report generation typically takes a few minutes depending on the time range selected.
"""

TOOL_DESCRIPTION = """Create a performance report for an RDS instance.

    This tool creates a performance analysis report for a specific RDS instance over a time period
    that can range from 5 minutes to 6 days. Creating performance reports is an asynchronous process.
    The created reports will be tagged for identification.

    <use_case>
    Use this tool to generate detailed performance analysis reports for your RDS instances.
    These reports can help identify performance bottlenecks, analyze database behavior patterns,
    and support optimization efforts.
    </use_case>

    <important_notes>
    1. Currently ONLY available for RDS for PostgreSQL instances
    2. The analysis period can range from 5 minutes to 6 days
    3. There must be at least 24 hours of performance data before the analysis start time
    4. Time parameters must be in ISO8601 format (e.g., '2025-06-01T00:00:00Z')
    5. This operation will not be registered if the --read-only flag is True
    6. For region, DB engine, and instance class support information, see Amazon RDS documentation
    </important_notes>

    Args:
        dbi_resource_identifier: The DbiResourceId of a RDS Instance (e.g., db-EXAMPLEDBIID)
        start_time: The beginning of the time interval for the report (ISO8601 format)
        end_time: The end of the time interval for the report (ISO8601 format)

    Returns:
        str: A confirmation message with the report ID and instructions to access the report

    <examples>
    Example usage scenarios:
    1. Performance troubleshooting:
       - Generate a report for a period where performance issues were observed
       - Analyze the detailed metrics to identify bottlenecks

    2. Capacity planning:
       - Create reports for peak usage periods
       - Use the insights to make informed scaling decisions

    3. Performance optimization:
       - Generate reports before and after configuration changes
       - Compare the results to validate improvements
    </examples>
"""


@mcp.tool(
    name='CreateRDSPerformanceReport',
    description=TOOL_DESCRIPTION,
    annotations=ToolAnnotations(
        title='CreateRDSPerformanceReport',
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
    ),
)
@handle_exceptions
async def create_rds_performance_report(
    dbi_resource_identifier: str = Field(
        ...,
        description='The DbiResourceId of a RDS Instance (e.g., db-EXAMPLEDBIID) for the data source where PI should get its metrics.',
    ),
    start_time: Optional[str] = Field(
        None,
        description='The beginning of the time interval for the report (ISO8601 format). This must be within 5 minutes to 6 days of the end_time. There must be at least 24 hours of performance data before the analysis start time.',
    ),
    end_time: Optional[str] = Field(
        None,
        description='The end of the time interval for the report (ISO8601 format). This must be within 5 minutes to 6 days of the start_time.',
    ),
    tags: Optional[List[Dict[str, str]]] = Field(
        [],
        description='Optional list of tags to apply to the new report. A tag indicating that this report was created by this MCP server is automatically added.',
    ),
) -> str:
    """Create a performance analysis report for a specific RDS instance.

    This function initiates the creation of a performance analysis report for the specified
    RDS instance over the given time period. The report generation is asynchronous and
    will continue after this function returns.

    Args:
        dbi_resource_identifier: The DbiResourceId of the RDS instance to analyze
        start_time: The beginning of the time interval for the report (ISO8601 format)
        end_time: The end of the time interval for the report (ISO8601 format)
        tags: Optional list of tags to apply to the new report. A tag indicating that this report was created by this MCP server is automatically added.

    Returns:
        str: A confirmation message with the report ID and access instructions

    Raises:
        ValueError: If running in readonly mode or if parameters are invalid
    """
    if Context.readonly_mode():
        logger.warning('You are running this tool in readonly mode. This operation is not allowed')
        raise ValueError(
            'You have configured this tool in readonly mode. To make this change you will have to update your configuration.'
        )

    start = convert_string_to_datetime(
        default=datetime.now() - timedelta(days=5), date_string=start_time
    )
    end = convert_string_to_datetime(
        default=datetime.now() - timedelta(days=2), date_string=end_time
    )

    report_tags = [MCP_SERVER_TAG]
    if tags:
        for tag_item in tags:
            for key, value in tag_item.items():
                report_tags.append({'Key': key, 'Value': value})

    pi_client = PIConnectionManager.get_connection()
    response = pi_client.create_performance_analysis_report(
        ServiceType='RDS',
        Identifier=dbi_resource_identifier,
        StartTime=start,
        EndTime=end,
        Tags=report_tags,
    )

    report_id = response.get('AnalysisReportId')

    return REPORT_CREATION_SUCCESS_RESPONSE.format(report_id)
