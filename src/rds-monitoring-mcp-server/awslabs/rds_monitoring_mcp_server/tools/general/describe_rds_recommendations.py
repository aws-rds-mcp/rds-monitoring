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

import json
from ...common.connection import RDSConnectionManager
from ...common.decorators import handle_exceptions
from ...common.server import mcp
from ...common.utils import convert_datetime_to_string
from ...context import Context
from loguru import logger
from mcp.types import ToolAnnotations
from mypy_boto3_rds.type_defs import DBRecommendationTypeDef, RecommendedActionTypeDef
from pydantic import BaseModel, Field
from typing import List, Literal, Optional


# Data Models


class SimplifiedMetric(BaseModel):
    """A simplified metric relevant to a recommendation."""

    name: str = Field(..., description='Name of the metric (e.g., CPUUtilization, FreeableMemory)')
    statistics_details: str = Field(
        ...,
        description='The details of different statistics for a metric. The description might contain markdown.',
    )


class RecommendedAction(BaseModel):
    """A simplified model representing a recommended action.

    Contains only the essential information needed for LLM summarization.
    """

    title: str = Field(..., description='The title of the action')
    description: Optional[str] = Field(None, description='The description of the action')
    relevant_metrics: Optional[List[SimplifiedMetric]] = Field(
        None, description='Key metrics directly relevant to this recommendation'
    )


class DBRecommendation(BaseModel):
    """A simplified model for RDS database recommendations designed for LLM summarization.

    Contains only the essential information needed for summarizing RDS recommendations,
    removing detailed technical information that's not crucial for high-level understanding.
    """

    recommendation_id: str = Field(..., description='The unique identifier for the recommendation')
    severity: str = Field(
        ..., description="Severity level: 'high', 'medium', 'low', or 'informational'"
    )
    status: str = Field(
        ...,
        description="Status: 'active' (ready to apply), 'pending' (in progress), 'resolved' (completed), or 'dismissed'",
    )
    created_time: str = Field(..., description='The time when the recommendation was created')
    updated_time: str = Field(..., description='The time when the recommendation was last updated')

    # Core content fields
    detection: Optional[str] = Field(None, description='Short description of the issue identified')
    recommendation: Optional[str] = Field(
        None, description='Short description of how to resolve the issue'
    )
    description: Optional[str] = Field(
        None, description='Detailed description of the recommendation'
    )
    reason: Optional[str] = Field(
        None, description='The reason why this recommendation was created'
    )
    category: Optional[str] = Field(
        None,
        description="Category: 'performance efficiency', 'security', 'reliability', 'cost optimization', 'operational excellence', or 'sustainability'",
    )
    impact: Optional[str] = Field(
        None, description='Short description that explains the possible impact of an issue'
    )

    # Simplified actions
    recommended_actions: Optional[List[RecommendedAction]] = Field(
        None, description='The list of recommended actions to resolve the issues'
    )


class DBRecommendationList(BaseModel):
    """A simplified model representing a list of database recommendations for LLM summarization."""

    recommendations: List[DBRecommendation] = Field(
        ..., description='The list of simplified database recommendations'
    )
    count: int = Field(..., description='The number of recommendations.')


# Helper Functions


def extract_metrics(action_dict: RecommendedActionTypeDef) -> Optional[List[SimplifiedMetric]]:
    """Extract metrics information from recommendation issue details.

    Args:
        action_dict: Dictionary containing issue details from the AWS RDS API response

    Returns:
        Optional[List[SimplifiedMetric]]: A list of simplified metrics or None
    """
    metrics: Optional[List[SimplifiedMetric]] = None

    issue_details = action_dict.get('IssueDetails')
    if issue_details and issue_details.get('PerformanceIssueDetails'):
        perf_details = issue_details.get('PerformanceIssueDetails')
        if perf_details and perf_details.get('Metrics'):
            metrics_list: List[SimplifiedMetric] = []
            for metric_data in perf_details.get('Metrics', []):
                name = metric_data.get('Name')
                statistics_details = metric_data.get('StatisticsDetails')
                if name is not None and statistics_details is not None:
                    metric = SimplifiedMetric(
                        name=name,
                        statistics_details=statistics_details,
                    )
                    metrics_list.append(metric)
            metrics = metrics_list if metrics_list else None

    return metrics


def convert_action(
    action_dict: RecommendedActionTypeDef,
    relevant_metrics: Optional[List[SimplifiedMetric]] = None,
) -> RecommendedAction:
    """Convert an action dict from the AWS RDS API to a RecommendedAction model.

    Args:
        action_dict: The action dict from the AWS RDS API response
        relevant_metrics: Optional list of metrics relevant to this action

    Returns:
        RecommendedAction: A model representing the action
    """
    return RecommendedAction(
        title=action_dict.get('Title', ''),
        description=action_dict.get('Description'),
        relevant_metrics=relevant_metrics,
    )


def convert_to_dbrecommendation(rec: DBRecommendationTypeDef) -> DBRecommendation:
    """Convert a recommendation dict from the AWS RDS API to a DBRecommendation model.

    Args:
        rec: The recommendation dict from the AWS RDS API response

    Returns:
        DBRecommendation: A model representing the recommendation
    """
    recommended_actions: List[RecommendedAction] = []

    if rec.get('RecommendedActions'):
        recommended_actions: List[RecommendedAction] = []
        for action_dict in rec.get('RecommendedActions', []):
            action_metrics = extract_metrics(action_dict)
            action = convert_action(action_dict, action_metrics if action_metrics else [])

            # Skip empty actions where title is empty and both description and relevant_metrics are null
            if (
                action.title == ''
                and action.description is None
                and action.relevant_metrics is None
            ):
                continue

            recommended_actions.append(action)

    recommendation = DBRecommendation(
        recommendation_id=rec.get('RecommendationId', ''),
        severity=rec.get('Severity', ''),
        status=rec.get('Status', ''),
        created_time=convert_datetime_to_string(rec.get('CreatedTime')),
        updated_time=convert_datetime_to_string(rec.get('UpdatedTime')),
        detection=rec.get('Detection'),
        recommendation=rec.get('Recommendation'),
        description=rec.get('Description'),
        reason=rec.get('Reason'),
        category=rec.get('Category'),
        impact=rec.get('Impact'),
        recommended_actions=recommended_actions,
    )

    return recommendation


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
    recommendations = []
    rds_client = RDSConnectionManager.get_connection()
    paginator = rds_client.get_paginator('describe_db_recommendations')

    params = {}
    if last_updated_after:
        params['LastUpdatedAfter'] = last_updated_after
    if last_updated_before:
        params['LastUpdatedBefore'] = last_updated_before

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

    page_iterator = paginator.paginate(**params, PaginationConfig=Context.get_pagination_config())
    count = 0

    for page in page_iterator:
        for rec in page.get('DBRecommendations', []):
            db_recommendation = convert_to_dbrecommendation(rec)
            recommendations.append(db_recommendation)
            count += 1

    recommendation_list = DBRecommendationList(recommendations=recommendations, count=count)

    logger.info(f'Retrieved {count} recommendations')
    serializable_dict = recommendation_list.model_dump()
    return json.dumps(serializable_dict, indent=2)
