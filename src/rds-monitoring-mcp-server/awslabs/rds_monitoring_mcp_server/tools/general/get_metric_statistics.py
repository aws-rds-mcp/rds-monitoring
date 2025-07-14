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

"""get_metric_statistics helpers, data models and tool implementation."""

from ...common.connection import CloudwatchConnectionManager
from ...common.decorators import handle_exceptions
from ...common.server import mcp
from ...common.utils import convert_string_to_datetime
from datetime import datetime, timedelta
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


# Data Models


class MetricDimension(BaseModel):
    """A model representing a CloudWatch metric dimension."""

    Name: str = Field(..., description='The name of the dimension')
    Value: str = Field(..., description='The value of the dimension')


class MetricDatapoint(BaseModel):
    """A model representing a CloudWatch metric datapoint."""

    Timestamp: datetime = Field(..., description='The timestamp for the datapoint')
    Average: Optional[float] = Field(None, description='The average value')
    Sum: Optional[float] = Field(None, description='The sum value')
    Maximum: Optional[float] = Field(None, description='The maximum value')
    Minimum: Optional[float] = Field(None, description='The minimum value')
    SampleCount: Optional[float] = Field(None, description='The sample count')
    Unit: Optional[str] = Field(None, description='The unit of measurement')
    ExtendedStatistics: Optional[Dict[str, float]] = Field(None, description='Extended statistics')


class MetricStatisticsResult(BaseModel):
    """A model representing CloudWatch metric statistics result."""

    Label: str = Field(..., description='The human-readable label for the metric')
    Datapoints: List[MetricDatapoint] = Field(..., description='The metric datapoints')


# Helper Functions


def format_dimensions(
    dimensions: Optional[List[Dict[str, str]]],
) -> Optional[List[MetricDimension]]:
    """Format dimensions to ensure proper structure."""
    if not dimensions:
        return None

    formatted_dimensions = []
    for d in dimensions:
        if 'Name' in d and 'Value' in d:
            formatted_dimensions.append(MetricDimension(**d))
        else:
            for k, v in d.items():
                formatted_dimensions.append(MetricDimension(Name=k, Value=v))
    return formatted_dimensions


# Core function without MCP decorators for testing
async def _get_metric_statistics_core(
    metric_name: str,
    start_time: str,
    end_time: str,
    period: int,
    namespace: str = 'AWS/RDS',
    dimensions: Optional[List[Dict[str, str]]] = None,
    statistics: Optional[List[str]] = None,
    extended_statistics: Optional[List[str]] = None,
    unit: Optional[str] = None,
) -> MetricStatisticsResult:
    """Core implementation without MCP decorators."""
    start = convert_string_to_datetime(
        default=datetime.now() - timedelta(hours=1), date_string=start_time
    )
    end = convert_string_to_datetime(default=datetime.now(), date_string=end_time)

    params: Dict[str, Any] = {
        'Namespace': namespace,
        'MetricName': metric_name,
        'StartTime': start,
        'EndTime': end,
        'Period': period,
    }

    formatted_dimensions = format_dimensions(dimensions)
    if formatted_dimensions:
        params['Dimensions'] = [dim.model_dump() for dim in formatted_dimensions]
    if statistics:
        params['Statistics'] = statistics
    if extended_statistics:
        params['ExtendedStatistics'] = extended_statistics
    if unit:
        params['Unit'] = unit

    cloudwatch_client = CloudwatchConnectionManager.get_connection()
    response = cloudwatch_client.get_metric_statistics(**params)

    datapoints = [MetricDatapoint(**dp) for dp in response.get('Datapoints', [])]
    return MetricStatisticsResult(Label=response.get('Label', ''), Datapoints=datapoints)


# MCP Tool

TOOL_DESCRIPTION = """Retrieve CloudWatch metric statistics for monitoring and analysis.

    This tool fetches time-series data points for CloudWatch metrics across various AWS services.
    It supports filtering by dimensions, multiple statistics types, and custom time ranges.

    <use_case>
    Use this tool to monitor resource performance over time, analyze metric trends and patterns,
    retrieve data for custom dashboards, and troubleshoot performance issues.
    </use_case>

    <important_notes>
    1. Maximum 1440 data points per request
    2. Period must be multiple of 60 seconds
    3. Start time must be before end time
    4. Dimensions must be properly formatted with Name and Value keys
    5. Choose appropriate statistics based on the metric type
    </important_notes>

    Args:
        metric_name: The name of the metric (e.g., 'CPUUtilization', 'DatabaseConnections')
        start_time: The start time in ISO 8601 format (e.g., '2024-01-01T00:00:00Z')
        end_time: The end time in ISO 8601 format (e.g., '2024-01-01T01:00:00Z')
        period: The granularity in seconds (60, 300, 3600, etc.)
        namespace: The CloudWatch namespace (default: 'AWS/RDS')
        dimensions: List of dimension filters [{'Name': 'DBInstanceIdentifier', 'Value': 'mydb'}]
        statistics: Basic statistics ['Average', 'Sum', 'Maximum', 'Minimum', 'SampleCount']
        extended_statistics: Percentile statistics ['p50', 'p90', 'p95', 'p99']
        unit: The unit for the metric (e.g., 'Percent', 'Count', 'Bytes')

    Returns:
        str: A JSON string containing metric label and datapoints with timestamps and values

    <examples>
    Example usage scenarios:
    1. Monitor database performance:
       - Retrieve CPU utilization for an RDS instance over the last hour
       - Analyze memory usage trends during peak hours

    2. Troubleshoot performance issues:
       - Examine I/O metrics during reported slow periods
       - Compare connection counts before and after an incident
    </examples>
    """


@mcp.tool(
    name='GetMetricStatistics',
    description=TOOL_DESCRIPTION,
    annotations=ToolAnnotations(
        title='GetMetricStatistics',
        readOnlyHint=True,
    ),
)
@handle_exceptions
async def get_metric_statistics(
    metric_name: str = Field(..., description='The name of the metric'),
    start_time: str = Field(..., description='The start time in ISO 8601 format'),
    end_time: str = Field(..., description='The end time in ISO 8601 format'),
    period: int = Field(..., description='The granularity in seconds'),
    namespace: str = Field(default='AWS/RDS', description='The CloudWatch namespace'),
    dimensions: Optional[List[Dict[str, str]]] = Field(
        None, description='List of dimension filters'
    ),
    statistics: Optional[List[str]] = Field(None, description='Basic statistics to retrieve'),
    extended_statistics: Optional[List[str]] = Field(None, description='Percentile statistics'),
    unit: Optional[str] = Field(None, description='The unit for the metric'),
) -> MetricStatisticsResult:
    """Get CloudWatch metric statistics.

    Args:
        metric_name: The name of the metric
        start_time: The start time in ISO 8601 format
        end_time: The end time in ISO 8601 format
        period: The granularity in seconds
        namespace: The CloudWatch namespace
        dimensions: List of dimension filters
        statistics: Basic statistics to retrieve
        extended_statistics: Percentile statistics
        unit: The unit for the metric

    Returns:
        MetricStatisticsResult: The metric statistics result
    """
    return await _get_metric_statistics_core(
        metric_name=metric_name,
        start_time=start_time,
        end_time=end_time,
        period=period,
        namespace=namespace,
        dimensions=dimensions,
        statistics=statistics,
        extended_statistics=extended_statistics,
        unit=unit,
    )
