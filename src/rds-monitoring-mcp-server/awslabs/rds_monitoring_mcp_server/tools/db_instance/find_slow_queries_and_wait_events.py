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

"""find_slow_queries_and_wait_events data models, helpers and tool implementation."""

from ...common.connection import PIConnectionManager
from ...common.decorators.handle_exceptions import handle_exceptions
from ...common.server import mcp
from ...common.utils import convert_string_to_datetime
from datetime import datetime, timedelta
from loguru import logger
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Literal, Optional


# Data Models


class MetricDataPoint(BaseModel):
    """Represents a single data point in a time series metric."""

    timestamp: str = Field(..., description='ISO8601 formatted timestamp')
    value: float = Field(..., description='The metric value at this timestamp')


class DimensionDetails(BaseModel):
    """Represents dimension details for a metric result."""

    dimension_key: str = Field(
        ..., description='The dimension key (e.g., wait event name or SQL ID)'
    )
    dimension_value: str = Field(..., description='The dimension value (full text or description)')
    additional_info: Optional[Dict[str, Any]] = Field(
        None, description='Additional information about the dimension'
    )


class MetricResult(BaseModel):
    """Represents a single metric result with its dimensions and data points."""

    metric_name: str = Field(..., description='The name of the metric (e.g., db.load.avg)')
    dimensions: Dict[str, str] = Field(
        ..., description='The dimensions associated with this metric result'
    )
    datapoints: List[MetricDataPoint] = Field(
        ..., description='Time series data points for this metric'
    )
    average_value: Optional[float] = Field(
        None, description='Average value calculated from all data points'
    )


class SlowQueriesAndWaitEventsResponse(BaseModel):
    """Response model for slow queries and wait events analysis."""

    resource_identifier: str = Field(..., description='The DbiResourceId of the analyzed instance')
    dimension: str = Field(
        ..., description='The dimension used for grouping (db.wait_event or db.sql_tokenized)'
    )
    calculation: str = Field(..., description='The calculation method used (avg, min, max, sum)')
    time_range: Dict[str, str] = Field(
        ..., description='The time range of the analysis with start and end timestamps'
    )
    period_seconds: int = Field(..., description='The granularity of data points in seconds')
    results: List[MetricResult] = Field(
        ..., description='List of metric results sorted by average value descending'
    )
    count: int = Field(..., description='Total number of results returned')


# Helper Functions


def build_metric_queries(
    dimension: str,
    calculation: str,
    limit: int,
) -> List[Dict[str, Any]]:
    """Build Performance Insights metric queries.

    Args:
        dimension: The dimension to group by ('db.wait_event' or 'db.sql_tokenized')
        calculation: The aggregate calculation method ('avg', 'min', 'max', 'sum')
        limit: Maximum number of items to return

    Returns:
        List of metric query dictionaries for the Performance Insights API
    """
    metric_name = f'db.load.{calculation}'

    return [
        {
            'Metric': metric_name,
            'GroupBy': {
                'Group': dimension,
                'Limit': limit,
            },
        }
    ]


def process_metric_results(
    metric_list: List[Dict[str, Any]],
    dimension: str,
    limit: int,
) -> List[MetricResult]:
    """Process raw metric results into structured MetricResult objects.

    Args:
        metric_list: Raw metric results from Performance Insights API
        dimension: The dimension used for grouping
        limit: Maximum number of results to return

    Returns:
        List of processed MetricResult objects
    """
    results = []

    for metric_result in metric_list:
        dimension_details = metric_result.get('Key', {}).get('Dimensions', {})

        # Skip results with empty dimensions when we're looking for grouped results
        if not dimension_details:
            continue

        # Filter datapoints to only include non-zero values
        datapoints = []
        raw_datapoints = metric_result.get('DataPoints', [])

        for dp in raw_datapoints:
            value = dp.get('Value', 0)
            # Only include datapoints with non-zero values
            if value > 0:
                timestamp = dp['Timestamp']
                if isinstance(timestamp, datetime):
                    timestamp = timestamp.isoformat()

                datapoints.append(
                    MetricDataPoint(
                        timestamp=timestamp,
                        value=value,
                    )
                )

        # Only include results that have non-zero datapoints
        if not datapoints:
            continue

        average_value = sum(dp.value for dp in datapoints) / len(datapoints)

        result = MetricResult(
            metric_name=metric_result.get('Key', {}).get('Metric', ''),
            dimensions=dimension_details,
            datapoints=datapoints,
            average_value=average_value,
        )

        results.append(result)

    # Sort by average value descending and apply limit
    results.sort(key=lambda x: x.average_value or 0, reverse=True)
    return results[:limit]


# MCP Tool Args

TOOL_DESCRIPTION = """Find slow queries and wait events in RDS databases.

    Use this tool to troubleshoot database performance issues by identifying which SQL queries are consuming the most database resources and wait events are causing delays in query execution.

    <important_notes>
        1. Requires Performance Insights to be enabled on the RDS instance. Getting a NotAuthorizedException means that PI might not be enabled on the instance.
        2. SQL statements larger than 500 bytes will be truncated in the response
    </important_notes>
"""


@mcp.tool(
    name='FindSlowQueriesAndWaitEvents',
    description=TOOL_DESCRIPTION,
    annotations=ToolAnnotations(
        title='Find Slow Queries and Wait Events',
        readOnlyHint=True,
    ),
)
@handle_exceptions
async def find_slow_queries_and_wait_events(
    dbi_resource_identifier: str = Field(
        ...,
        description='The DbiResourceId of the RDS instance (e.g., db-EXAMPLEDBIID) to analyze for performance issues',
    ),
    dimension: Literal['db.wait_event', 'db.sql_tokenized'] = Field(
        ...,
        description='The dimension to group by. Use "db.wait_event" for wait events or "db.sql_tokenized" for SQL queries',
    ),
    calculation: Literal['avg', 'min', 'max', 'sum'] = Field(
        ...,
        description='The aggregate calculation method to apply to the DBLoad metric',
    ),
    start_time: Optional[str] = Field(
        None,
        description='The beginning of the time interval to analyze (ISO8601 format, e.g., "2025-06-01T00:00:00Z")',
    ),
    end_time: Optional[str] = Field(
        None,
        description='The end of the time interval to analyze (ISO8601 format, e.g., "2025-06-01T12:00:00Z")',
    ),
    period_in_seconds: Literal[1, 60, 300, 3600, 86400] = Field(
        300,
        description='The granularity of data points in seconds (1=per second, 60=per minute, 300=5 minutes, 3600=hourly, 86400=daily)',
    ),
    limit: int = Field(
        10,
        description='Maximum number of items to return for the dimension group (1-50)',
        ge=1,
        le=50,
    ),
) -> SlowQueriesAndWaitEventsResponse:
    """Find slow queries and wait events in RDS databases using Performance Insights.

    This function queries RDS Performance Insights to identify top SQL queries or wait events
    that are contributing to database load. It returns metrics grouped by the specified dimension
    to help diagnose performance bottlenecks.

    Args:
        dbi_resource_identifier: The DbiResourceId of the RDS instance
        dimension: The dimension to group by ('db.wait_event' or 'db.sql_tokenized')
        calculation: The aggregate calculation method ('avg', 'min', 'max', or 'sum')
        start_time: The beginning of the time interval (ISO8601 format)
        end_time: The end of the time interval (ISO8601 format)
        period_in_seconds: The granularity of data points
        limit: Maximum number of items to return


    Returns:
        str: A JSON string containing the analysis results

    Raises:
        ValueError: If Performance Insights is not enabled or parameters are invalid
    """
    # Handle FieldInfo objects that may be passed instead of actual values during unit tests
    start_time_value = start_time if isinstance(start_time, str) else None
    end_time_value = end_time if isinstance(end_time, str) else None
    period_seconds_value = period_in_seconds if isinstance(period_in_seconds, int) else 300
    limit_value = limit if isinstance(limit, int) else 10

    now = datetime.now()
    start = convert_string_to_datetime(
        default=now - timedelta(hours=1), date_string=start_time_value
    )
    end = convert_string_to_datetime(default=now, date_string=end_time_value)

    metric_queries = build_metric_queries(dimension, calculation, limit_value)

    pi_client = PIConnectionManager.get_connection()

    response = pi_client.get_resource_metrics(
        ServiceType='RDS',
        Identifier=dbi_resource_identifier,
        MetricQueries=metric_queries,
        StartTime=start,
        EndTime=end,
        PeriodInSeconds=period_in_seconds,
    )

    metric_results = process_metric_results(
        metric_list=response.get('MetricList', []),
        dimension=dimension,
        limit=limit_value,
    )

    result = SlowQueriesAndWaitEventsResponse(
        resource_identifier=dbi_resource_identifier,
        dimension=dimension,
        calculation=calculation,
        time_range={
            'start': start.isoformat(),
            'end': end.isoformat(),
        },
        period_seconds=period_seconds_value,
        results=metric_results,
        count=len(metric_results),
    )

    logger.info(
        f'Retrieved {len(metric_results)} {dimension} results for {dbi_resource_identifier} '
        f'from {start.isoformat()} to {end.isoformat()}'
    )

    return result
