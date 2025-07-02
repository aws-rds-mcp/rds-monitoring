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

import json
from ...common.connection import PIConnectionManager
from ...common.decorators import handle_exceptions
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


def fetch_full_sql_text(
    pi_client: Any,
    dbi_resource_identifier: str,
    dimension: str,
    dimension_key: str,
    dimension_value: str,
) -> str:
    """Fetch the full SQL text for a tokenized SQL statement.

    Args:
        pi_client: The Performance Insights client
        dbi_resource_identifier: The DbiResourceId of the RDS instance
        dimension: The dimension group ('db.sql_tokenized')
        dimension_key: The SQL statement ID
        dimension_value: The current tokenized value

    Returns:
        The full SQL text if available, otherwise the original tokenized value
    """
    try:
        sql_details = pi_client.get_dimension_key_details(
            ServiceType='RDS',
            Identifier=dbi_resource_identifier,
            Group=dimension,
            GroupIdentifier=dimension_key,
            RequestedDimensions=[dimension_key],
        )

        if 'Dimensions' in sql_details:
            return sql_details['Dimensions'].get(dimension_key, dimension_value)

        return dimension_value

    except Exception as e:
        logger.warning(f'Could not retrieve full SQL for {dimension_key}: {e}')
        return dimension_value


def process_metric_results(
    metric_list: List[Dict[str, Any]],
    dimension: str,
    full_sql_statement: bool,
    pi_client: Any,
    dbi_resource_identifier: str,
) -> List[MetricResult]:
    """Process raw metric results into structured MetricResult objects.

    Args:
        metric_list: Raw metric results from Performance Insights API
        dimension: The dimension used for grouping
        full_sql_statement: Whether to fetch full SQL text
        pi_client: The Performance Insights client
        dbi_resource_identifier: The DbiResourceId

    Returns:
        List of processed MetricResult objects
    """
    results = []

    for metric_result in metric_list:
        dimension_details = metric_result.get('Key', {}).get('Dimensions', {})

        if dimension == 'db.sql_tokenized' and full_sql_statement:
            updated_dimensions = {}
            for dimension_key, dimension_value in dimension_details.items():
                full_text = fetch_full_sql_text(
                    pi_client,
                    dbi_resource_identifier,
                    dimension,
                    dimension_key,
                    dimension_value,
                )
                updated_dimensions[dimension_key] = full_text
            dimension_details = updated_dimensions

        datapoints = []
        raw_datapoints = metric_result.get('DataPoints', [])

        for dp in raw_datapoints:
            timestamp = dp['Timestamp']
            if isinstance(timestamp, datetime):
                timestamp = timestamp.isoformat()

            datapoints.append(
                MetricDataPoint(
                    timestamp=timestamp,
                    value=dp['Value'],
                )
            )

        average_value = None
        if datapoints:
            average_value = sum(dp.value for dp in datapoints) / len(datapoints)

        result = MetricResult(
            metric_name=metric_result.get('Key', {}).get('Metric', ''),
            dimensions=dimension_details,
            datapoints=datapoints,
            average_value=average_value,
        )

        results.append(result)

    results.sort(key=lambda x: x.average_value or 0, reverse=True)

    return results


# MCP Tool Args

TOOL_DESCRIPTION = """Find slow queries and wait events in RDS databases.

    This tool analyzes RDS Performance Insights data to identify slow-running queries and
    wait events that are consuming database resources. It uses the DBLoad metric to measure
    session activity and provides insights into performance bottlenecks.

    <use_case>
    Use this tool to troubleshoot database performance issues by identifying:
    - Which SQL queries are consuming the most database resources
    - What wait events are causing delays in query execution
    - Patterns of database load over time to understand performance trends
    - Specific queries that need optimization or tuning
    </use_case>

    <important_notes>
    1. Requires Performance Insights to be enabled on the RDS instance. Use the aws-rds://db-instance/{db_instance_identifier} to check this. Getting a NotAuthorizedException means that PI might not be enabled on the instance.
    2. The DBLoad metric shows the number of active sessions for the database engine
    3. Wait events indicate where database work is being impeded (e.g., I/O, locks, CPU)
    4. Top SQL dimension shows which queries contribute most to database load
    6. By default returns tokenized SQL for security; set full_sql_statement=True for full text
    7. SQL statements larger than 500 bytes will be truncated in the response
    </important_notes>

    Args:
        dbi_resource_identifier: The DbiResourceId of the RDS instance (e.g., db-EXAMPLEDBIID)
        dimension: The dimension to group by ('db.wait_event' for wait events or 'db.sql_tokenized' for SQL queries)
        calculation: The aggregate calculation method ('avg', 'min', 'max', or 'sum')
        start_time: The beginning of the time interval (ISO8601 format)
        end_time: The end of the time interval (ISO8601 format)
        period_in_seconds: The granularity of data points (1, 60, 300, 3600, or 86400 seconds)
        limit: Maximum number of items to return for the dimension group (default: 10)
        full_sql_statement: Whether to retrieve full SQL text instead of tokenized (default: False)

    Returns:
        str: A JSON string containing the slow queries or wait events analysis

    <examples>
    Example usage scenarios:
    1. Identify top wait events during a performance issue:
       - Set dimension to 'db.wait_event'
       - Analyze which wait types are causing delays

    2. Find slow queries consuming resources:
       - Set dimension to 'db.sql_tokenized'
       - Review the top SQL statements by load

    3. Correlate wait events with specific queries:
       - Run the tool twice with different dimensions
       - Compare timestamps to identify problematic query patterns
    </examples>
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
    full_sql_statement: bool = Field(
        False,
        description='Whether to retrieve full SQL text instead of tokenized. Set to True to see complete SQL statements',
    ),
) -> str:
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
        full_sql_statement: Whether to retrieve full SQL text

    Returns:
        str: A JSON string containing the analysis results

    Raises:
        ValueError: If Performance Insights is not enabled or parameters are invalid
    """
    start = convert_string_to_datetime(
        default=datetime.now() - timedelta(hours=1), date_string=start_time
    )
    end = convert_string_to_datetime(default=datetime.now(), date_string=end_time)

    metric_queries = build_metric_queries(dimension, calculation, limit)

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
        full_sql_statement=full_sql_statement,
        pi_client=pi_client,
        dbi_resource_identifier=dbi_resource_identifier,
    )

    response_model = SlowQueriesAndWaitEventsResponse(
        resource_identifier=dbi_resource_identifier,
        dimension=dimension,
        calculation=calculation,
        time_range={
            'start': start.isoformat(),
            'end': end.isoformat(),
        },
        period_seconds=period_in_seconds,
        results=metric_results,
        count=len(metric_results),
    )

    logger.info(
        f'Retrieved {len(metric_results)} {dimension} results for {dbi_resource_identifier} '
        f'from {start.isoformat()} to {end.isoformat()}'
    )

    serializable_dict = response_model.model_dump()
    return json.dumps(serializable_dict, indent=2)
