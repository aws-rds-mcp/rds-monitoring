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

"""describe_rds_recommendations helpers, data models and tool implementation."""

from ...common.connection import RDSConnectionManager
from ...common.decorators.handle_exceptions import handle_exceptions
from ...common.server import mcp
from ...common.utils import convert_string_to_datetime, handle_paginated_aws_api_call
from datetime import datetime
from mcp.types import ToolAnnotations
from mypy_boto3_rds.type_defs import DBRecommendationTypeDef
from pydantic import BaseModel, Field
from typing import List, Literal, Optional


class DBRecommendationList(BaseModel):
    """A simplified model representing a list of database recommendations for LLM summarization."""

    recommendations: List[DBRecommendationTypeDef] = Field(
        ..., description='The list of simplified database recommendations'
    )
    count: int = Field(..., description='The number of recommendations.')


# MCP Tool Args

TOOL_DESCRIPTION = """Get RDS recommendations.

    This tool retrieves recommendations for RDS resources such as DB instances and clusters.
    Recommendations include operational suggestions, performance improvements, and best practices
    tailored to your specific RDS resources.

    <use_case>
    Use this tool to discover potential improvements and best practices for your RDS resources.
    Recommendations can help optimize performance, reduce costs, improve availability, and enhance
    security of your RDS databases.
    </use_case>

    <important_notes>
    1. You can filter recommendations by various criteria including status, severity, and resource IDs
    2. Time-based filters use ISO8601 format (e.g., '2025-06-01T00:00:00Z')
    3. Recommendations are categorized by severity to help prioritize actions
    4. Each recommendation includes detailed descriptions and specific actions to take
    </important_notes>

    Args:
        ctx: The MCP context object for handling the request and providing access to server utilities
        last_updated_after: Filter to include recommendations updated after this time (ISO8601 format)
        last_updated_before: Filter to include recommendations updated before this time (ISO8601 format)
        status: Filter by recommendation status ('active', 'pending', 'resolved', 'dismissed')
        severity: Filter by recommendation severity ('high', 'medium', 'low', 'informational')
        cluster_resource_id: Filter by cluster resource identifier
        dbi_resource_id: Filter by database instance resource identifier

    Returns:
        str: A JSON string containing a list of recommendations for the specified resources

    <examples>
    Example usage scenarios:
    1. Discover performance improvement opportunities:
       - Retrieve all active recommendations for a specific DB instance
       - Identify areas where database performance can be enhanced

    2. Security recommendations:
       - Find all security-related recommendations by filtering on category or keywords
       - Address high-severity security recommendations as a priority

    3. Cost optimization:
       - Find recommendations related to instance sizing and utilization
       - Identify opportunities to reduce costs through resource optimization
    </examples>
"""

# MCP Tool


@mcp.tool(
    name='DescribeRDSRecommendations',
    description=TOOL_DESCRIPTION,
    annotations=ToolAnnotations(
        title='DescribeRDSRecommendations',
        readOnlyHint=True,
    ),
)
@handle_exceptions
async def describe_rds_recommendations(
    last_updated_after: Optional[str] = Field(
        None,
        description='Filter to include recommendations updated after this time (ISO8601 format)',
    ),
    last_updated_before: Optional[str] = Field(
        None,
        description='Filter to include recommendations updated before this time (ISO8601 format)',
    ),
    status: Optional[Literal['active', 'pending', 'resolved', 'dismissed']] = Field(
        None, description='Filter by recommendation status'
    ),
    severity: Optional[Literal['high', 'medium', 'low', 'informational']] = Field(
        None, description='Filter by recommendation severity'
    ),
    cluster_resource_id: Optional[str] = Field(
        None, description='Filter by cluster resource identifier'
    ),
    dbi_resource_id: Optional[str] = Field(
        None, description='Filter by database instance resource identifier'
    ),
) -> str:
    """Retrieve RDS recommendations and convert them to simplified models suitable for LLM summarization and insights.

    Args:
        rds_client: The boto3 RDS client for making API calls
        last_updated_after: Filter to include recommendations updated after this time
        last_updated_before: Filter to include recommendations updated before this time
        status: Filter by recommendation status ('active', 'pending', 'resolved', 'dismissed')
        severity: Filter by recommendation severity ('high', 'medium', 'low', 'informational')
        cluster_resource_id: Filter by cluster resource identifier
        dbi_resource_id: Filter by database instance resource identifier
        ctx: Optional context for error handling and logging

    Returns:
        DBRecommendationList: A model containing the list of recommendations designed for LLM processing
    """
    params = {}
    if last_updated_after:
        params['LastUpdatedAfter'] = convert_string_to_datetime(datetime.now(), last_updated_after)
    if last_updated_before:
        params['LastUpdatedBefore'] = convert_string_to_datetime(
            datetime.now(), last_updated_before
        )

    filters = []
    if status:
        filters.append({'Name': 'status', 'Values': [status]})
    if severity:
        filters.append({'Name': 'severity', 'Values': [severity]})
    if cluster_resource_id:
        filters.append({'Name': 'cluster-resource-id', 'Values': [cluster_resource_id]})
    if dbi_resource_id:
        filters.append({'Name': 'dbi-resource-id', 'Values': [dbi_resource_id]})

    if filters:
        params['Filters'] = filters

    rds_client = RDSConnectionManager.get_connection()

    recommendations = handle_paginated_aws_api_call(
        client=rds_client,
        paginator_name='describe_db_recommendations',
        operation_parameters=params,
        result_key='DBRecommendations',
    )

    recommendation_list = DBRecommendationList(
        recommendations=recommendations, count=len(recommendations)
    )

    return recommendation_list
