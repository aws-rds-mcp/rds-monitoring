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

"""Event-related functions for the RDS Monitoring MCP Server."""

import json
from awslabs.rds_monitoring_mcp_server.constants import MAX_ITEMS
from awslabs.rds_monitoring_mcp_server.models import DBEvent, DBEventList
from awslabs.rds_monitoring_mcp_server.utils import handle_aws_error
from datetime import datetime
from mypy_boto3_rds import RDSClient
from mypy_boto3_rds.type_defs import EventTypeDef
from typing import List, Literal, Optional


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


async def describe_rds_events(
    rds_client: RDSClient,
    source_identifier: str,
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
    ],
    event_categories: Optional[List[str]] = None,
    duration: Optional[int] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
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

    Returns:
        str: A JSON string containing a list of events in the database
    """
    params = {
        'SourceIdentifier': source_identifier,
        'SourceType': source_type,
        'MaxRecords': MAX_ITEMS,
    }

    if event_categories:
        params['EventCategories'] = event_categories
    if duration:
        params['Duration'] = duration
    if start_time:
        params['StartTime'] = start_time
    if end_time:
        params['EndTime'] = end_time

    try:
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
    except Exception as e:
        error_result = await handle_aws_error(
            f'describe_events({source_identifier, source_type})', e, None
        )
        return json.dumps(error_result, indent=2)
