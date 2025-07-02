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

"""describe_rds_events helpers, data models and tool implementation."""

import json
from ...common.connection import RDSConnectionManager
from ...common.decorators import handle_exceptions
from ...common.server import mcp
from ...context import Context
from datetime import datetime
from mcp.server.fastmcp import Context as ctx
from mcp.types import ToolAnnotations
from mypy_boto3_rds.type_defs import EventTypeDef
from pydantic import BaseModel, Field
from typing import List, Literal, Optional


# Data Models


class DBEvent(BaseModel):
    """A model representing a database event."""

    message: str = Field(..., description='Text of this event')
    event_categories: List[str] = Field(..., description='Categories for the event')
    date: str = Field(..., description='Date and time of the event')
    source_arn: Optional[str] = Field(
        None, description='The Amazon Resource Name (ARN) for the event'
    )


class DBEventList(BaseModel):
    """A model representing the response of the describe_rds_events function."""

    source_identifier: str = Field(..., description='Identifier for the source of the event')
    source_type: Literal[
        'db-instance',
        'db-parameter-group',
        'db-security-group',
        'db-snapshot',
        'db-cluster',
        'db-cluster-snapshot',
        'custom-engine-version',
        'db-proxy',
        'blue-green-deployment',
    ]
    events: List[DBEvent] = Field(..., description='List of DB events')
    count: int = Field(..., description='Total number of events')


# Helper Function


def format_event(event: EventTypeDef) -> DBEvent:
    """Format an event from the AWS API into a DBEvent model.

    Args:
        event: The event dictionary from the AWS API

    Returns:
        DBEvent: The formatted event
    """
    # Handle date conversion carefully
    date_value = event.get('Date')
    if date_value is None:
        formatted_date = ''
    elif isinstance(date_value, datetime):
        formatted_date = date_value.isoformat()
    else:
        formatted_date = str(date_value)

    return DBEvent(
        message=event.get('Message', ''),
        event_categories=event.get('EventCategories', []),
        date=formatted_date,
        source_arn=event.get('SourceArn'),
    )


# MCP Tool Args

TOOL_DESCRIPTION = """List events for an RDS resource.

    This tool retrieves events for RDS resources such as DB instances, clusters,
    security groups, etc. Events can be filtered by source identifier, category,
    time period, and source type.

    <use_case>
    Use this tool to monitor and troubleshoot RDS resources by retrieving event information.
    Events include operational activities, status changes, and notifications about your
    RDS resources.
    </use_case>

    <important_notes>
    1. You must provide a valid source_identifier and source_type
    2. For time-based filtering, you can use either duration or start_time/end_time, but not both
    3. Duration is limited to 14 days (20160 minutes) in the past
    4. Start and end times must be in ISO8601 format
    5. Use the event categories to filter specific types of events (backup, configuration change, etc.)
    </important_notes>

    Args:
        ctx: The MCP context object for handling the request and providing access to server utilities
        source_identifier: The identifier of the event source (e.g., DB instance or DB cluster)
        source_type: The type of source ('db-instance', 'db-security-group', 'db-parameter-group',
                    'db-snapshot', 'db-cluster', or 'db-cluster-snapshot')
        event_categories: The categories of events (e.g., 'backup', 'configuration change', etc.)
        duration: The number of minutes in the past to retrieve events
        start_time: The beginning of the time interval to retrieve events (ISO8601 format)
        end_time: The end of the time interval to retrieve events (ISO8601 format)

    Returns:
        str: A JSON string containing a list of events for the specified resource

    <examples>
    Example usage scenarios:
    1. View recent events for a DB instance:
       - Retrieve events from the last 24 hours for a specific instance
       - Check for any configuration changes or maintenance activities

    2. Investigate issues with a DB cluster:
       - Look for failover events during a specific time period
       - Check for connectivity or availability issues reported in events

    3. Monitor backup status:
       - Filter events by the 'backup' category to verify successful backups
       - Identify any backup failures or issues
    </examples>
"""

# MCP Tool


@mcp.tool(
    name='DescribeRDSEvents',
    description=TOOL_DESCRIPTION,
    annotations=ToolAnnotations(
        title='DescribeRDSEvents',
        readOnlyHint=True,
    ),
)
@handle_exceptions
async def describe_rds_events(
    ctx: ctx,
    source_identifier: str = Field(
        ...,
        description='The identifier of the event source (e.g., DBInstanceIdentifier or DBClusterIdentifier). A valid identifier must be provided.',
    ),
    source_type: Literal[
        'db-instance',
        'db-parameter-group',
        'db-security-group',
        'db-snapshot',
        'db-cluster',
        'db-cluster-snapshot',
        'custom-engine-version',
        'db-proxy',
        'blue-green-deployment',
    ] = Field(..., description='The type of source'),
    event_categories: Optional[List[str]] = Field(
        None, description='The categories of events (e.g., backup, configuration change)'
    ),
    duration: Optional[int] = Field(
        None,
        description='The number of minutes in the past to retrieve events (up to 14 days/20160 minutes)',
    ),
    start_time: Optional[str] = Field(
        None, description='The beginning of the time interval to retrieve events (ISO8601 format)'
    ),
    end_time: Optional[str] = Field(
        None, description='The end of the time interval to retrieve events (ISO8601 format)'
    ),
) -> str:
    """List events for an RDS resource.

    This function retrieves events for RDS resources such as DB instances, clusters,
    security groups, etc. Events can be filtered by source identifier, category,
    time period, and source type.

    Args:
        rds_client: The boto3 RDS client to use for making API calls
        source_identifier: The identifier of the event source (e.g., DB instance or DB cluster)
        source_type: The type of source ('db-instance', 'db-security-group', 'db-parameter-group',
                    'db-snapshot', 'db-cluster', or 'db-cluster-snapshot')
        event_categories: List of categories of events (e.g., 'backup', 'configuration change', etc.)
        duration: The number of minutes in the past to retrieve events (up to 14 days/20160 minutes)
        start_time: The beginning of the time interval to retrieve events
        end_time: The end of the time interval to retrieve events
        ctx: The MCP context object for error handling and logging

    Returns:
        str: A JSON string containing a list of events in the database
    """
    params = {
        'SourceIdentifier': source_identifier,
        'SourceType': source_type,
        'MaxRecords': Context.max_items(),
    }

    if event_categories:
        params['EventCategories'] = event_categories
    if duration:
        params['Duration'] = duration
    if start_time:
        params['StartTime'] = start_time
    if end_time:
        params['EndTime'] = end_time

    rds_client = RDSConnectionManager.get_connection()
    response = rds_client.describe_events(**params)
    raw_events = response.get('Events', [])
    processed_events = [format_event(event) for event in raw_events]
    result = DBEventList(
        events=processed_events,
        count=len(processed_events),
        source_identifier=source_identifier,
        source_type=source_type,
    )
    serializable_dict = result.model_dump()
    return json.dumps(serializable_dict, indent=2)
