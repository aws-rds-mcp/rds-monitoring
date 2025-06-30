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

import logging
from awslabs.rds_monitoring_mcp_server.constants import PAGINATION_CONFIG
from awslabs.rds_monitoring_mcp_server.models import DetailedMetricItem, MessageDetail
from awslabs.rds_monitoring_mcp_server.utils import convert_string_to_datetime
from datetime import datetime, timedelta
from mypy_boto3_cloudwatch import CloudWatchClient
from pydantic import Field
from typing import Any, Dict, List, Literal, Optional


# Set up logging
logger = logging.getLogger(__name__)


INSTANCE_METRICS = [
    'CPUUtilization',
    'FreeableMemory',
    'DatabaseConnections',
    'NetworkThroughput',
    'ReadIOPS',
    'WriteIOPS',
    'ReadLatency',
    'WriteLatency',
    'FreeLocalStorage',
]

CLUSTER_METRICS = [
    'AuroraVolumeBytesLeftTotal',
    'VolumeBytesUsed',
    'VolumeReadIOPs',
    'VolumeWriteIOPs',
]

GLOBAL_CLUSTER_METRICS = [
    'AuroraGlobalDBReplicationLag',
    'AuroraGlobalDBReplicatedWriteIO',
    'AuroraGlobalDBRPOLag',
    'AuroraGlobalDBProgressLag',
]


async def get_metric_statistics(
    cloudwatch_client: CloudWatchClient,
    metric_name: str,
    start_time: str,
    end_time: str,
    period: int,
    dimensions: Optional[List[Dict[str, str]]] = None,
    statistics: Optional[List[str]] = None,
    extended_statistics: Optional[List[str]] = None,
    unit: Optional[str] = None,
) -> Dict[str, Any]:
    """Get CloudWatch metric statistics.

    Args:
        cloudwatch_client: The CloudWatch client to use for API calls
        metric_name: The name of the metric
        start_time: The start time in ISO 8601 format
        end_time: The end time in ISO 8601 format
        period: The granularity, in seconds, of the returned data points
        dimensions: The dimensions to filter by
        statistics: The metric statistics to return
        extended_statistics: The percentile statistics to return
        unit: The unit for the metric

    Returns:
        Dict containing metric statistics
    """
    # Convert ISO 8601 strings to datetime objects
    start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
    end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))

    # Build request parameters
    params: Dict[str, Any] = {
        'Namespace': 'AWS/ElastiCache',
        'MetricName': metric_name,
        'StartTime': start,
        'EndTime': end,
        'Period': period,
    }

    # Add optional parameters
    if dimensions:
        # Ensure dimensions are properly formatted as [{'Name': name, 'Value': value}, ...]
        formatted_dimensions = []
        for d in dimensions:
            # Check if the dimension is already in the correct format
            if 'Name' in d and 'Value' in d:
                formatted_dimensions.append(d)
            else:
                # Convert from {key: value} format to {'Name': key, 'Value': value}
                for k, v in d.items():
                    formatted_dimensions.append({'Name': k, 'Value': v})
        params['Dimensions'] = formatted_dimensions
    if statistics:
        params['Statistics'] = statistics
    if extended_statistics:
        params['ExtendedStatistics'] = extended_statistics
    if unit:
        params['Unit'] = unit

    # Make API call
    response = cloudwatch_client.get_metric_statistics(**params)

    # Extract relevant information
    datapoints = response.get('Datapoints', [])
    label = response.get('Label')

    result = {'Label': label, 'Datapoints': datapoints}

    return result


def build_metric_queries(
    resource_type: str,
    resource_identifier: str,
    start_date: datetime,
    end_date: datetime,
    period: int,
    stat: str,
):
    """Build CloudWatch metric queries for RDS resources.

    Args:
        resource_type: The type of RDS resource ('instance', 'cluster', or 'global_cluster')
        resource_identifier: The identifier of the RDS resource
        start_date: The start time for the metrics query
        end_date: The end time for the metrics query
        period: The granularity, in seconds, of the returned datapoints
        stat: The statistic to retrieve for the specified metrics

    Returns:
        List of metric query dictionaries configured for the specified resource
    """
    if resource_type == 'instance':
        dimension_name = 'DBInstanceIdentifier'
        metrics = INSTANCE_METRICS
    elif resource_type == 'cluster':
        metrics = CLUSTER_METRICS
        dimension_name = 'DBClusterIdentifier'
    else:
        metrics = GLOBAL_CLUSTER_METRICS
        dimension_name = 'DBClusterIdentifier'

    metric_queries = []
    for metric in metrics:
        metric_query = {
            'Id': f'metric_{metric}_{stat}',
            'MetricStat': {
                'Metric': {
                    'Namespace': 'AWS/RDS',
                    'MetricName': metric,
                    'Dimensions': [{'Name': dimension_name, 'Value': resource_identifier}],
                },
                'Period': period,
                'Stat': stat,
                'Unit': 'Count',
            },
            'ReturnData': True,
        }
        metric_queries.append(metric_query)

    return metric_queries


def process_metric_data(metric_data: Dict[str, Any]) -> DetailedMetricItem:
    """Convert a CloudWatch metric data dictionary to a DetailedMetricItem model."""
    # Extract the required fields from the metric data dictionary
    messages = []
    if 'Messages' in metric_data and metric_data['Messages']:
        for msg in metric_data['Messages']:
            messages.append(MessageDetail(code=msg.get('Code', ''), value=msg.get('Value', '')))

    # Create and return the DetailedMetricItem model
    return DetailedMetricItem(
        id=metric_data.get('Id', ''),
        label=metric_data.get('Label', ''),
        timestamps=metric_data.get('Timestamps', []),
        values=metric_data.get('Values', []),
        status_code=metric_data.get('StatusCode', 'Complete'),
        messages=messages if messages else None,
    )


async def describe_rds_performance_metrics(
    cloudwatch_client: CloudWatchClient,
    resource_identifier: str = Field(
        ...,
        description='The identifier of the RDS resource (DBInstanceIdentifier or DBClusterIdentifier)',
    ),
    resource_type: Literal['instance', 'cluster', 'global_cluster'] = Field(
        ...,
        description='Type of RDS resource to fetch metrics for (instance, cluster, or global_cluster)',
    ),
    start_date: str = Field(
        ...,
        description='The start time for the metrics query in ISO 8601 format (e.g., 2025-06-01T00:00:00Z)',
    ),
    end_date: str = Field(
        ...,
        description='The end time for the metrics query in ISO 8601 format (e.g., 2025-06-29T00:00:00Z)',
    ),
    period: int = Field(
        ...,
        description='The granularity, in seconds, of the returned datapoints (e.g., 60 for per-minute data)',
    ),
    stat: Literal['SampleCount', 'Sum', 'Average', 'Minimum', 'Maximum'] = Field(
        ...,
        description='The statistic to retrieve for the specified metric (SampleCount, Sum, Average, Minimum, or Maximum)',
    ),
    scan_by: Literal['TimestampDescending', 'TimestampAscending'] = Field(
        ...,
        description='The order to scan the results by timestamp (newest first or oldest first)',
    ),
) -> List[DetailedMetricItem]:
    """Describe RDS performance metrics.

    This tool retrieves performance metrics for RDS resources such as DB instances, clusters,
    and global clusters. Metrics can be filtered by resource identifier, resource type,
    time period, and statistic.

    <use_case>
    Use this tool to monitor and troubleshoot RDS resources by retrieving performance metrics.
    Metrics include CPU utilization, free memory, database connections, network throughput,
    and other relevant RDS metrics.
    <use_case>
    """
    start = convert_string_to_datetime(
        default=datetime.now() - timedelta(days=7), date_string=start_date
    )
    end = convert_string_to_datetime(default=datetime.now(), date_string=end_date)

    metric_queries = build_metric_queries(
        resource_type, resource_identifier, start, end, period, stat
    )

    paginator = cloudwatch_client.get_paginator('get_metric_data')
    response_iterator = paginator.paginate(
        MetricDataQueries=metric_queries,
        StartTime=start,
        EndTime=end,
        ScanBy=scan_by,
        PaginationConfig=PAGINATION_CONFIG,
    )

    results: List[DetailedMetricItem] = []  # Initialize as an empty list

    for response in response_iterator:
        for metric_data_dict in response['MetricDataResults']:
            results.append(process_metric_data(metric_data_dict))

    return results
