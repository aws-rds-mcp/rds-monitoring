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

"""awslabs RDS Control Plane Operations MCP Server."""

import os
import sys
from awslabs.rds_monitoring_mcp_server.clients import (
    get_cloudwatch_client,
    get_pi_client,
    get_rds_client,
)
from awslabs.rds_monitoring_mcp_server.discovery import (
    get_cluster_details,
    get_instance_details,
    list_clusters,
    list_instances,
)
from awslabs.rds_monitoring_mcp_server.events import describe_rds_events
from awslabs.rds_monitoring_mcp_server.recommendations import get_recommendations
from datetime import datetime
from loguru import logger
from mcp.server.fastmcp import Context, FastMCP
from pydantic import Field
from typing import List, Literal, Optional


# Remove all default handlers then add our own
logger.remove()
logger.add(sys.stderr, level='INFO')

global pi_client
global rds_client
global cloudwatch_client

try:
    pi_client = get_pi_client(
        region_name=os.getenv('AWS_REGION'),
        profile_name=os.getenv('AWS_PROFILE'),
    )
    rds_client = get_rds_client(
        region_name=os.getenv('AWS_REGION'),
        profile_name=os.getenv('AWS_PROFILE'),
    )
    cloudwatch_client = get_cloudwatch_client(
        region_name=os.getenv('AWS_REGION'),
        profile_name=os.getenv('AWS_PROFILE'),
    )
except Exception as e:
    logger.error(f'Error getting RDS, PI or CloudWatch clients: {e}')
    raise e

mcp = FastMCP(
    'RDS Monitoring',
    instructions="""
    The AWS Labs RDS Control Plane Operations MCP Server provides access to Amazon RDS Control Plane Operations for managing and monitoring database instances.

    ## Usage Workflow:
    1. ALWAYS start by accessing either the `resource://instances` or `resource://clusters`resource to discover available instances and clusters
    2. Note down the db_instance_identifier and db_cluster_identifier for use with monitoring and management tools

    ## Important Notes:
    - Instance names are case-sensitive
    - Always verify that the instance name exists in the resource response before querying
    """,
    dependencies=['pydantic', 'loguru', 'boto3'],
)


@mcp.resource(uri='aws-rds://db-instance', name='ListInstances', mime_type='application/json')
async def list_instances_resource() -> List[dict]:
    """List all available Amazon RDS instances in your account.

    <use_case>
    Use this resource to discover all available RDS database instances in your AWS account. The list includes both standalone instances and instances that
    are part of Aurora clusters.
    </use_case>

    <important_notes>
    1. The response provides the essential information (identifiers, engine, etc.) about each instance
    2. Instance identifiers returned can be used with other tools and resources in this MCP server
    3. Keep note of the DBInstanceIdentifier and DbiResourceId for use with other tools
    4. Instances are filtered to the AWS region specified in your environment configuration
    5. Use the `aws-rds://db-instance/{db_instance_identifier}` resource to get more information (networking, cluster membership details etc.) about a specific instance
    </important_notes>

    ## Response structure
    Returns an array of DB instance objects, each containing:
    - `DBInstanceIdentifier`: Unique identifier for the instance (string)
    - `DbiResourceId`: The unqiue resource identifier for this instance (string)
    - `DBInstanceArn`: ARN of the instance (string)
    - `DBInstanceStatus`: Current status of the instance (string)
    - `DBInstanceClass`: The compute and memory capacity class (string)
    - `Engine`: Database engine type (string)
    - `AvailabilityZone`: The AZ where the instance resides (string)
    - `MultiAZ`: Whether the instance is Multi-AZ (boolean)
    - `TagList`: List of tags attached to the instance

    <examples>
    Example usage scenarios:
    1. Discovery and inventory:
       - List all available RDS instances to create an inventory

    2. Preparation for other operations:
       - Find specific instance identifiers to use with performance monitoring tools
       - Identify instances to check for events or read logs from
    </examples>
    """
    return await list_instances(rds_client=rds_client)


@mcp.resource(
    uri='aws-rds://db-instance/{db_instance_identifier}',
    name='GetInstanceDetails',
    mime_type='application/json',
)
async def instance_details_resource(db_instance_identifier: str) -> dict:
    """Get detailed information about a specific RDS instance.

    <use_case>
    Use this resource to retrieve comprehensive details about a specific RDS instance,
    including its networking, configuration, and performance metrics.
    </use_case>

    <important_notes>
    1. The response provides the essential information (identifiers, engine, etc.) about each instance
    2. Instance identifiers returned can be used with other tools and resources in this MCP server
    3. Keep note of the DBInstanceIdentifier and DbiResourceId for use with other tools
    4. Instances are filtered to the AWS region specified in your environment configuration
    5. Use the `aws-rds://db-instance/{db_instance_identifier}` to get more information about a specific instance
    </important_notes>

    ## Response structure
    Returns an array of DB instance objects, each containing:
    - `DBInstanceIdentifier`: Unique identifier for the instance (string)
    - `DbiResourceId`: The unique resource identifier for this instance (string)
    - `DBInstanceArn`: ARN of the instance (string)
    - `DBInstanceStatus`: Current status of the instance (string)
    - `DBInstanceClass`: The compute and memory capacity class (string)
    - `Engine`: Database engine type (string)
    - `AvailabilityZone`: The AZ where the instance resides (string)
    - `MultiAZ`: Whether the instance is Multi-AZ (boolean)
    - `TagList`: List of tags attached to the instance

    <examples>
    Example usage scenarios:
    1. Discovery and inventory:
       - List all available RDS instances to create an inventory

    2. Preparation for other operations:
       - Find specific instance identifiers to use with performance monitoring tools
       - Identify instances that may need maintenance or upgrades
    </examples>
    """
    return await get_instance_details(
        rds_client=rds_client, db_instance_identifier=db_instance_identifier
    )


@mcp.resource(uri='aws-rds://db-cluster', name='ListClusters', mime_type='application/json')
async def list_clusters_resource() -> List[dict]:
    """List all available Amazon RDS clusters in your account.

    <use_case>
    Use this resource to discover all available RDS database clusters in your AWS account,
    including Aurora clusters (MySQL/PostgreSQL) and Multi-AZ DB clusters.
    </use_case>

    <important_notes>
    1. The response provides the essential information (identifiers, engine, etc.) about each cluster
    2. Cluster identifiers returned can be used with other tools and resources in this MCP server
    3. Keep note of the db_cluster_identifier and db_cluster_resource_id for use with other tools
    4. Clusters are filtered to the AWS region specified in your environment configuration
    5. Use the `aws-rds://db-cluster/{db_cluster_identifier}` to get more information about a specific cluster
    </important_notes>

    ## Response structure
    Returns an array of DB cluster objects, each containing:
    - `db_cluster_identifier`: Unique identifier for the cluster (string)
    - `db_cluster_resource_id`: The unique resource identifier for this cluster (string)
    - `db_cluster_arn`: ARN of the cluster (string)
    - `status`: Current status of the cluster (string)
    - `engine`: Database engine type (string)
    - `engine_version`: The version of the database engine (string)
    - `availability_zones`: The AZs where the cluster instances can be created (array of strings)
    - `multi_az`: Whether the cluster has instances in multiple Availability Zones (boolean)
    - `tag_list`: List of tags attached to the cluster

    <examples>
    Example usage scenarios:
    1. Discovery and inventory:
       - List all available RDS clusters to create an inventory
       - Identify cluster engine types and versions in your environment

    2. Preparation for other operations:
       - Find specific cluster identifiers to use with management tools
       - Identify clusters that may need maintenance or upgrades
    </examples>
    """
    return await list_clusters(rds_client=rds_client)


@mcp.resource(
    uri='aws-rds://db-cluster/{db_cluster_identifier}',
    name='GetClusterDetails',
    mime_type='application/json',
)
async def cluster_details_resource(db_cluster_identifier: str) -> dict:
    """Get detailed information about a specific RDS cluster.

    <use_case>
    Use this resource to retrieve comprehensive details about a specific RDS cluster,
    including its instances, networking, and configuration.
    </use_case>

    <important_notes>
    1. The response provides the essential information (identifiers, engine, etc.) about each cluster
    2. Cluster identifiers returned can be used with other tools and resources in this MCP server
    3. Keep note of the db_cluster_identifier and db_cluster_resource_id for use with other tools
    4. Clusters are filtered to the AWS region specified in your environment configuration
    5. Use the `aws-rds://db-cluster/{db_cluster_identifier}` to get more information about a specific cluster
    </important_notes>

    ## Response structure
    Returns an array of DB cluster objects, each containing:
    - `db_cluster_identifier`: Unique identifier for the cluster (string)
    - `db_cluster_resource_id`: The unique resource identifier for this cluster (string)
    - `db_cluster_arn`: ARN of the cluster (string)
    - `status`: Current status of the cluster (string)
    - `engine`: Database engine type (string)
    - `engine_version`: The version of the database engine (string)
    - `availability_zones`: The AZs where the cluster instances can be created (array of strings)
    - `multi_az`: Whether the cluster has instances in multiple Availability Zones (boolean)
    - `tag_list`: List of tags attached to the cluster

    <examples>
    Example usage scenarios:
    1. Discovery and inventory:
       - List all available RDS clusters to create an inventory
       - Identify cluster engine types and versions in your environment

    2. Preparation for other operations:
       - Find specific cluster identifiers to use with management tools
       - Identify clusters that may need maintenance or upgrades
    </examples>
    """
    return await get_cluster_details(
        rds_client=rds_client, cluster_identifier=db_cluster_identifier
    )


@mcp.tool(
    name='DescribeRDSResourceEvents',
)
async def describe_rds_resource_events_tool(
    ctx: Context,
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
    # Convert string datetime to python datetime objects if provided
    start_time_dt = None if start_time is None else datetime.fromisoformat(start_time)
    end_time_dt = None if end_time is None else datetime.fromisoformat(end_time)

    return await describe_rds_events(
        rds_client=rds_client,
        source_identifier=source_identifier,
        source_type=source_type,
        event_categories=event_categories,
        duration=duration,
        start_time=start_time_dt,
        end_time=end_time_dt,
        ctx=ctx,
    )


@mcp.tool(
    name='GetRDSRecommendations',
)
async def get_rds_recommendations_tool(
    ctx: Context,
    last_updated_after: Optional[str] = Field(
        None,
        description='Filter to include recommendations updated after this time (ISO8601 format)',
    ),
    last_updated_before: Optional[str] = Field(
        None,
        description='Filter to include recommendations updated before this time (ISO8601 format)',
    ),
    status: Optional[Literal['active', 'pending', 'resolved', 'dismissed']] = Field(
        None, description='Filter by recommendation status'
    ),
    severity: Optional[Literal['high', 'medium', 'low', 'informational']] = Field(
        None, description='Filter by recommendation severity'
    ),
    cluster_resource_id: Optional[str] = Field(
        None, description='Filter by cluster resource identifier'
    ),
    dbi_resource_id: Optional[str] = Field(
        None, description='Filter by database instance resource identifier'
    ),
) -> str:
    """Get RDS recommendations.

    This tool retrieves recommendations for RDS resources such as DB instances and clusters.
    Recommendations include operational suggestions, performance improvements, and best practices
    tailored to your specific RDS resources.

    <use_case>
    Use this tool to discover potential improvements and best practices for your RDS resources.
    Recommendations can help optimize performance, reduce costs, improve availability, and enhance
    security of your RDS databases.
    </use_case>

    <important_notes>
    1. You can filter recommendations by various criteria including status, severity, and resource IDs
    2. Time-based filters use ISO8601 format (e.g., '2025-06-01T00:00:00Z')
    3. Recommendations are categorized by severity to help prioritize actions
    4. Each recommendation includes detailed descriptions and specific actions to take
    </important_notes>

    Args:
        ctx: The MCP context object for handling the request and providing access to server utilities
        last_updated_after: Filter to include recommendations updated after this time (ISO8601 format)
        last_updated_before: Filter to include recommendations updated before this time (ISO8601 format)
        status: Filter by recommendation status ('active', 'pending', 'resolved', 'dismissed')
        severity: Filter by recommendation severity ('high', 'medium', 'low', 'informational')
        cluster_resource_id: Filter by cluster resource identifier
        dbi_resource_id: Filter by database instance resource identifier

    Returns:
        str: A JSON string containing a list of recommendations for the specified resources

    <examples>
    Example usage scenarios:
    1. Discover performance improvement opportunities:
       - Retrieve all active recommendations for a specific DB instance
       - Identify areas where database performance can be enhanced

    2. Security recommendations:
       - Find all security-related recommendations by filtering on category or keywords
       - Address high-severity security recommendations as a priority

    3. Cost optimization:
       - Find recommendations related to instance sizing and utilization
       - Identify opportunities to reduce costs through resource optimization
    </examples>
    """
    # Convert string datetime to python datetime objects if provided
    last_updated_after_dt = (
        None if last_updated_after is None else datetime.fromisoformat(last_updated_after)
    )
    last_updated_before_dt = (
        None if last_updated_before is None else datetime.fromisoformat(last_updated_before)
    )

    return await get_recommendations(
        rds_client=rds_client,
        last_updated_after=last_updated_after_dt,
        last_updated_before=last_updated_before_dt,
        status=status,
        severity=severity,
        cluster_resource_id=cluster_resource_id,
        dbi_resource_id=dbi_resource_id,
        ctx=ctx,
    )


def main():
    """Run the MCP server with CLI argument support."""
    mcp.run()


if __name__ == '__main__':
    main()
