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

"""describe_rds_performance_metrics helpers, data models and tool implementation."""

import json
from ...common.connection import CloudwatchConnectionManager
from ...common.decorators import handle_exceptions
from ...common.server import mcp
from ...common.utils import convert_string_to_datetime
from ...context import Context
from datetime import datetime, timedelta
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Literal, Optional


# A pre-configured list of metrics that would best describe the performance of a given RDS resource

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

# Data Models


class MessageDetail(BaseModel):
    """A model for a message associated with a metric data result."""

    code: str = Field(..., description='The error code or status code associated with the message')
    value: str = Field(..., description='The message text')


class DetailedMetricItem(BaseModel):
    """A model representing a metric data result from CloudWatch GetMetricData API.

    This model contains the detailed information about a specific metric's data points,
    including timestamps, values, and status information.
    """

    id: str = Field(..., description='The short name specified to represent this metric')
    label: str = Field(..., description='The human-readable label associated with the data')
    timestamps: List[datetime] = Field(..., description='The timestamps for the data points')
    values: List[float] = Field(
        ..., description='The data points for the metric corresponding to timestamps'
    )
    status_code: Literal['Complete', 'InternalError', 'PartialData', 'Forbidden'] = Field(
        ..., description='The status of the returned data'
    )
    messages: Optional[List[MessageDetail]] = Field(
        None, description='A list of messages with additional information about the data returned'
    )


class DetailedMetricItemList(BaseModel):
    """A model representing a collection of detailed metric items.

    This model contains a list of metric data results along with a count of the items.
    It is used to return multiple metrics in a structured format.
    """

    list: List[DetailedMetricItem] = Field(..., description='List of detailed metric items')
    count: int = Field(..., description='Number of metric items')


# Helper Functions


async def get_metric_statistics(
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
    cloudwatch_client = CloudwatchConnectionManager.get_connection()
    response = cloudwatch_client.get_metric_statistics(**params)

    # Extract relevant information
    datapoints = response.get('Datapoints', [])
    label = response.get('Label')

    result = {'Label': label, 'Datapoints': datapoints}

    return result


def build_metric_queries(
    resource_type: str,
    resource_identifier: str,
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


# MCP Tool Arg

TOOL_DESCRIPTION = """Retrieve performance metrics for RDS resources.

    This tool fetches detailed performance metrics for Amazon RDS resources including
    instances, clusters, and global clusters. It allows you to query metrics over a
    specified time period with configurable statistics and granularity.

    <use_case>
    Use this tool to monitor performance, analyze trends, and troubleshoot issues with your
    RDS databases. Performance metrics can help identify bottlenecks, resource constraints,
    and operational anomalies affecting your database workloads.
    </use_case>

    <important_notes>
    1. You must specify the correct resource_type that matches your resource_identifier
    2. Time range parameters (start_date and end_date) must be in ISO 8601 format
    3. Period (granularity) must match CloudWatch supported values (e.g., 60, 300, 3600)
    4. For Aurora clusters, certain metrics are only available at the cluster level
    5. Choose appropriate statistics based on the metric type (e.g., Average for CPU, Sum for counts)
    6. Consider using TimestampDescending for recent troubleshooting, TimestampAscending for historical analysis
    </important_notes>

    Args:
        resource_identifier: The identifier of the RDS resource (DBInstanceIdentifier or DBClusterIdentifier)
        resource_type: Type of RDS resource to fetch metrics for (instance, cluster, or global_cluster)
        start_date: The start time for the metrics query in ISO 8601 format (e.g., 2025-06-01T00:00:00Z)
        end_date: The end time for the metrics query in ISO 8601 format (e.g., 2025-06-29T00:00:00Z)
        period: The granularity, in seconds, of the returned datapoints (e.g., 60 for per-minute data)
        stat: The statistic to retrieve for the specified metric (SampleCount, Sum, Average, Minimum, or Maximum)
        scan_by: The order to scan the results by timestamp (newest first or oldest first)

    Returns:
        str: A JSON string containing the requested performance metrics data

    <examples>
    Example usage scenarios:
    1. Monitor database performance:
       - Retrieve CPU utilization metrics for a specific instance over the last hour
       - Analyze memory usage trends across a cluster during peak hours

    2. Troubleshoot performance issues:
       - Examine I/O metrics during reported slow periods
       - Compare database connection counts before and after an incident

    3. Capacity planning:
       - Analyze resource utilization trends over time to identify growth patterns
       - Determine if instances are appropriately sized based on workload metrics
    </examples>
    """


@mcp.tool(
    name='DescribeRDSPerformanceMetrics',
    description=TOOL_DESCRIPTION,
    annotations=ToolAnnotations(
        title='DescribeRDSPerformanceMetrics',
        readOnlyHint=True,
    ),
)
@handle_exceptions
async def describe_rds_performance_metrics(
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
) -> str:
    """Retrieve performance metrics for RDS resources.

    Args:
        resource_identifier: The identifier of the RDS resource (DBInstanceIdentifier or DBClusterIdentifier)
        resource_type: Type of RDS resource to fetch metrics for (instance, cluster, or global_cluster)
        start_date: The start time for the metrics query in ISO 8601 format (e.g., 2025-06-01T00:00:00Z)
        end_date: The end time for the metrics query in ISO 8601 format (e.g., 2025-06-29T00:00:00Z)
        period: The granularity, in seconds, of the returned datapoints (e.g., 60 for per-minute data)
        stat: The statistic to retrieve for the specified metric (SampleCount, Sum, Average, Minimum, or Maximum)
        scan_by: The order to scan the results by timestamp (newest first or oldest first)

    Returns:
        str: A JSON string containing the requested performance metrics data
    """
    start = convert_string_to_datetime(
        default=datetime.now() - timedelta(days=7), date_string=start_date
    )
    end = convert_string_to_datetime(default=datetime.now(), date_string=end_date)

    metric_queries = build_metric_queries(resource_type, resource_identifier, period, stat)

    cloudwatch_client = CloudwatchConnectionManager.get_connection()
    paginator = cloudwatch_client.get_paginator('get_metric_data')
    response_iterator = paginator.paginate(
        MetricDataQueries=metric_queries,
        StartTime=start,
        EndTime=end,
        ScanBy=scan_by,
        PaginationConfig=Context.get_pagination_config(),
    )

    results: List[DetailedMetricItem] = []  # Initialize as an empty list

    for response in response_iterator:
        for metric_data_dict in response['MetricDataResults']:
            results.append(process_metric_data(metric_data_dict))

    response_model = DetailedMetricItemList(
        list=results,
        count=len(results),
    )

    serializable_dict = response_model.model_dump()
    return json.dumps(serializable_dict, indent=2)
