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
from awslabs.rds_monitoring_mcp_server.monitoring.discovery import (
    list_clusters,
    list_instances,
)
from loguru import logger
from mcp.server.fastmcp import FastMCP
from typing import List


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


def main():
    """Run the MCP server with CLI argument support."""
    mcp.run()


if __name__ == '__main__':
    main()
