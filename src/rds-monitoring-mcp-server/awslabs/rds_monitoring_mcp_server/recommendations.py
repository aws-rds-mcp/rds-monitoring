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

"""Functionality to process, convert, and summarize RDS recommendations."""

import json
from awslabs.rds_monitoring_mcp_server.constants import PAGINATION_CONFIG
from awslabs.rds_monitoring_mcp_server.models import (
    DBRecommendation,
    DBRecommendationList,
    RecommendedAction,
    SimplifiedMetric,
)
from awslabs.rds_monitoring_mcp_server.utils import convert_datetime_to_string, handle_aws_error
from datetime import datetime
from loguru import logger
from mcp.server.fastmcp import Context
from mypy_boto3_rds import RDSClient
from mypy_boto3_rds.type_defs import DBRecommendationTypeDef, RecommendedActionTypeDef
from typing import List, Optional


def extract_metrics(action_dict: RecommendedActionTypeDef) -> Optional[List[SimplifiedMetric]]:
    """Extract metrics information from recommendation issue details.

    Args:
        action_dict: Dictionary containing issue details from the AWS RDS API response

    Returns:
        Optional[List[SimplifiedMetric]]: A list of simplified metrics or None
    """
    metrics = None

    if action_dict.get('IssueDetails') and action_dict['IssueDetails'].get(
        'PerformanceIssueDetails'
    ):
        perf_details = action_dict['IssueDetails']['PerformanceIssueDetails']
        if perf_details.get('Metrics'):
            metrics: List[SimplifiedMetric] = []
            for metric_data in perf_details['Metrics']:
                if metric_data.get('Name') and metric_data.get('StatisticsDetails'):
                    metric = SimplifiedMetric(
                        name=metric_data.get('Name'),
                        statistics_details=metric_data.get('StatisticsDetails'),
                    )
                    metrics.append(metric)

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
    relevant_metrics = extract_metrics(rec)
    recommended_actions = None

    if rec.get('RecommendedActions'):
        recommended_actions: List[RecommendedAction] = []
        for action_dict in rec['RecommendedActions']:
            action_metrics = extract_metrics(action_dict)
            action = convert_action(
                action_dict, action_metrics if action_metrics else relevant_metrics
            )

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


async def get_recommendations(
    rds_client: RDSClient,
    last_updated_after: Optional[datetime] = None,
    last_updated_before: Optional[datetime] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    cluster_resource_id: Optional[str] = None,
    dbi_resource_id: Optional[str] = None,
    ctx: Optional[Context] = None,
) -> DBRecommendationList:
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

    try:
        page_iterator = paginator.paginate(**params, PaginationConfig=PAGINATION_CONFIG)
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

    except Exception as e:
        error_result = await handle_aws_error('describe_db_recommendations', e, ctx=ctx)
        return json.dumps(error_result, indent=2)
