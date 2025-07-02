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

"""A helper function used by the cluster and instance list metrics resources."""

from awslabs.rds_monitoring_mcp_server.common.connection import CloudwatchConnectionManager
from pydantic import BaseModel, Field


class ListMetricItem(BaseModel):
    """A model for a metric included in the response of the availble metrics resources."""

    metric_name: str = Field(..., description='Name of the metric')
    recently_published_data_points: bool = Field(
        ...,
        description='Whether this metric has had data points published in the past three hours',
    )


async def list_metrics(dimension_name: str, dimension_value: str):
    """List available CloudWatch metrics for a given RDS resource.

    Args:
        dimension_name: The name of the dimension to filter metrics by (e.g., 'DBInstanceIdentifier')
        dimension_value: The value of the dimension to filter metrics by (e.g., instance ID)

    Returns:
        List of metrics as ListMetricItem objects with information about availability
        and recent activity
    """
    cloudwatch_client = CloudwatchConnectionManager.get_connection()
    paginator = cloudwatch_client.get_paginator('list_metrics')

    # Get all metrics for the dimension
    all_metrics_iterator = paginator.paginate(
        Namespace='AWS/RDS',
        Dimensions=[
            {'Name': dimension_name, 'Value': dimension_value},
        ],
    )

    # Get recently active metrics (past 3 hours)
    recent_metrics_iterator = paginator.paginate(
        Namespace='AWS/RDS',
        Dimensions=[
            {'Name': dimension_name, 'Value': dimension_value},
        ],
        RecentlyActive='PT3H',  # This is the only filter supported for RecentlyActive
    )

    # Collect recently active metric names
    recent_metric_names = set()
    for page in recent_metrics_iterator:
        for metric_dict in page['Metrics']:
            recent_metric_names.add(metric_dict['MetricName'])

    # Process all metrics and mark recently active ones
    metrics = []
    for page in all_metrics_iterator:
        for metric_dict in page['Metrics']:
            metric_item = ListMetricItem(
                metric_name=metric_dict['MetricName'],
                recently_published_data_points=metric_dict['MetricName'] in recent_metric_names,
            )
            metrics.append(metric_item)

    return metrics
