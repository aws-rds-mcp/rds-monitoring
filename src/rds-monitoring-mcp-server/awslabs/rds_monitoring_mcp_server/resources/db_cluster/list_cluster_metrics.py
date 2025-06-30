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

from ...common.decorators import handle_exceptions
from ...common.list_metrics import list_metrics
from ...common.server import mcp
from typing import List


RESOURCE_DESCRIPTION = """List available metrics for a RDS cluster.

    This tool retrieves a list of available metrics for a RDS cluster.

    <use_case>
    Use this tool to discover the available metrics for a RDS cluster.
    </use_case>

    <important_notes>
    1. The response provides the list of available metrics for the cluster
    2. Metrics are filtered to the AWS region specified in your environment configuration
    3. Use the `aws-rds://db-cluster/{db_cluster_identifier}/metrics/{metric_name}` to get more information about a specific metric
    </important_notes>

    Args:
        ctx: The MCP context object for handling the request and providing access to server utilities
        db_cluster_identifier: The identifier of the RDS cluster

    Returns:
        List[str]: A list of available metrics for the RDS cluster
    """


@mcp.resource(
    uri='aws-rds://db-cluster/{db_cluster_identifier}/available_metrics',
    name='ListClusterMetrics',
    description=RESOURCE_DESCRIPTION,
    mime_type='text/plain',
)
@handle_exceptions
async def list_cluster_metrics(db_cluster_identifier: str) -> List[str]:
    """List available metrics for an Amazon RDS cluster.

    This function retrieves a list of all available CloudWatch metrics for a specified
    RDS cluster. It uses the DB cluster identifier to filter metrics specifically for that cluster.

    Args:
        db_cluster_identifier (str): The identifier of the RDS cluster to retrieve metrics for.

    Returns:
        List[str]: A list of available metric names for the specified RDS cluster.
    """
    return await list_metrics(
        dimension_name='DBClusterIdentifier',
        dimension_value=db_cluster_identifier,
    )
