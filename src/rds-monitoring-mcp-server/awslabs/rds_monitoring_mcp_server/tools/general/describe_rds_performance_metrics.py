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

from ...common.connection import CloudwatchConnectionManager
from ...common.context import RDSContext
from ...common.decorators.handle_exceptions import handle_exceptions
from ...common.server import mcp
from ...common.utils import handle_paginated_aws_api_call
from datetime import datetime
from mcp.types import ToolAnnotations
from mypy_boto3_cloudwatch.literals import StatusCodeType
from mypy_boto3_cloudwatch.type_defs import MetricDataResultTypeDef
from pydantic import BaseModel, Field
from statistics import mean
from typing import List, Literal


METRICS = {
    'INSTANCE': [
        'BurstBalance',
        'CPUUtilization',
        'DatabaseConnections',
        'DiskQueueDepth',
        'FreeableMemory',
        'FreeStorageSpace',
        'ReadIOPS',
        'ReadLatency',
        'ReadThroughput',
        'SwapUsage',
        'WriteIOPS',
        'WriteLatency',
        'WriteThroughput',
        'TotalIOPS',
    ],
    'CLUSTER': [
        'AuroraVolumeBytesLeftTotal',
        'BackupRetentionPeriodStorageUsed',
        'ServerlessDatabaseCapacity',
        'SnapshotStorageUsed',
        'TotalBackupStorageBilled',
        'VolumeBytesUsed',
        'VolumeReadIOPs',
        'VolumeWriteIOPs',
    ],
    'GLOBAL_CLUSTER': [
        'AuroraGlobalDBReplicationLag',
        'AuroraGlobalDBReplicatedWriteIO',
        'AuroraGlobalDBRPOLag',
        'AuroraGlobalDBProgressLag',
    ],
}


class DataPoint(BaseModel):
    """Single metric data point with timestamp."""

    timestamp: datetime = Field(..., description='Timestamp of the data point')
    value: float = Field(..., description='Metric value at this timestamp')


class MetricSummary(BaseModel):
    """Metric data with statistics and raw data points."""

    id: str = Field(..., description='The metric identifier')
    label: str = Field(..., description='The human-readable label')
    data_status: StatusCodeType = Field(
        ...,
        description='Data retrieval status: Complete, PartialData, InternalError, or Forbidden',
    )
    current_value: float = Field(..., description='Most recent value')
    min_value: float = Field(..., description='Minimum value in period')
    max_value: float = Field(..., description='Maximum value in period')
    avg_value: float = Field(..., description='Average value in period')
    data_points_count: int = Field(..., description='Total number of data points available')
    sample_data_points: List[DataPoint] = Field(
        ...,
        description='Representative data points with timestamps for analysis, including first and last points plus evenly distributed samples',
    )

    @classmethod
    def from_metric_data(cls, metric_data: MetricDataResultTypeDef) -> 'MetricSummary':
        """Create MetricSummary from CloudWatch metric data.

        Args:
            metric_data: CloudWatch metric data result containing Values, Timestamps, StatusCode and other fields
        Returns:
            MetricSummary: Object containing summarized metric data
        """
        values = metric_data.get('Values', [])
        timestamps = metric_data.get('Timestamps', [])
        status = metric_data.get('StatusCode', 'Complete')
        if not values:
            return cls(
                id=metric_data.get('Id', ''),
                label=metric_data.get('Label', ''),
                data_status=status,
                current_value=0,
                min_value=0,
                max_value=0,
                avg_value=0,
                data_points_count=0,
                sample_data_points=[],
            )

        min_val, max_val, avg_val = min(values), max(values), mean(values)
        current_val = values[0] if timestamps and timestamps[0] > timestamps[-1] else values[-1]

        data_with_timestamps = list(zip(timestamps, values))
        data_with_timestamps.sort(key=lambda x: x[0])

        max_data_points = RDSContext.max_items()
        sample_data_points = []

        if len(data_with_timestamps) <= max_data_points:
            sample_data_points = [
                DataPoint(timestamp=ts, value=round(val, 2)) for ts, val in data_with_timestamps
            ]
        else:
            step = len(data_with_timestamps) // max_data_points
            sample_data_points = [
                DataPoint(
                    timestamp=data_with_timestamps[i][0],
                    value=round(data_with_timestamps[i][1], 2),
                )
                for i in range(0, len(data_with_timestamps), step)[:max_data_points]
            ]

            first_point = DataPoint(
                timestamp=data_with_timestamps[0][0], value=round(data_with_timestamps[0][1], 2)
            )
            last_point = DataPoint(
                timestamp=data_with_timestamps[-1][0], value=round(data_with_timestamps[-1][1], 2)
            )

            if sample_data_points and sample_data_points[0].timestamp != first_point.timestamp:
                sample_data_points.insert(0, first_point)
            if sample_data_points and sample_data_points[-1].timestamp != last_point.timestamp:
                sample_data_points.append(last_point)

        return cls(
            id=metric_data.get('Id', ''),
            label=metric_data.get('Label', ''),
            data_status=status,
            current_value=round(current_val, 2),
            min_value=round(min_val, 2),
            max_value=round(max_val, 2),
            avg_value=round(avg_val, 2),
            data_points_count=len(values),
            sample_data_points=sample_data_points,
        )


class MetricSummaryList(BaseModel):
    """List of metric data with representative data points."""

    metrics: List[MetricSummary] = Field(..., description='List of summarized metrics')
    resource_identifier: str = Field(..., description='RDS resource identifier')
    resource_type: str = Field(..., description='Resource type')
    time_period: str = Field(..., description='Query time period')


DESCRIBE_PERF_METRICS_TOOL_DESCRIPTION = """Retrieve performance metrics for RDS resources.
This tool fetches detailed performance metrics for Amazon RDS resources including instances, clusters, and global clusters, allowing you to monitor performance, analyze trends, and troubleshoot issues with your database workloads.
"""


@mcp.tool(
    name='DescribeRDSPerformanceMetrics',
    description=DESCRIBE_PERF_METRICS_TOOL_DESCRIPTION,
    annotations=ToolAnnotations(
        title='DescribeRDSPerformanceMetrics',
        readOnlyHint=True,
    ),
)
@handle_exceptions
def describe_rds_performance_metrics(
    resource_identifier: str = Field(
        ...,
        description='The identifier of the RDS resource (DBInstanceIdentifier or DBClusterIdentifier)',
    ),
    resource_type: Literal['INSTANCE', 'CLUSTER', 'GLOBAL_CLUSTER'] = Field(
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
) -> MetricSummaryList:
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
        MetricSummaryList: Performance metrics with statistical summaries and raw data points
    """
    start = (
        datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if start_date.endswith('Z')
        else datetime.fromisoformat(start_date)
    )
    end = (
        datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        if end_date.endswith('Z')
        else datetime.fromisoformat(end_date)
    )

    dimension_name = (
        'DBInstanceIdentifier' if resource_type == 'INSTANCE' else 'DBClusterIdentifier'
    )

    metrics = METRICS[resource_type]

    metric_queries = [
        {
            'Id': f'metric_{metric}_{stat}',
            'MetricStat': {
                'Metric': {
                    'Namespace': 'AWS/RDS',
                    'MetricName': metric,
                    'Dimensions': [{'Name': dimension_name, 'Value': resource_identifier}],
                },
                'Period': period,
                'Stat': stat,
            },
            'ReturnData': True,
        }
        for metric in metrics
    ]
    cloudwatch_client = CloudwatchConnectionManager.get_connection()

    results = handle_paginated_aws_api_call(
        client=cloudwatch_client,
        paginator_name='get_metric_data',
        operation_parameters={
            'MetricDataQueries': metric_queries,
            'StartTime': start,
            'EndTime': end,
            'ScanBy': scan_by,
            'PaginationConfig': RDSContext.get_pagination_config(),
        },
        format_function=MetricSummary.from_metric_data,
        result_key='MetricDataResults',
    )

    return MetricSummaryList(
        metrics=results,
        resource_identifier=resource_identifier,
        resource_type=resource_type,
        time_period=f'{start_date} to {end_date}',
    )
