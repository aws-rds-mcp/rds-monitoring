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

"""Resource for retrieving detailed information about RDS DB Clusters."""

import asyncio
from ...common.connection import RDSConnectionManager
from ...common.decorators.handle_exceptions import handle_exceptions
from ...common.decorators.register_mcp_primitive import register_mcp_primitive_by_context
from loguru import logger
from mypy_boto3_rds.type_defs import DBClusterTypeDef
from pydantic import BaseModel, Field
from typing import Optional


DESCRIBE_CLUSTER_DETAIL_RESOURCE_DESCRIPTION = """Get detailed information about a specific Amazon RDS cluster.

This resource retrieves comprehensive details about a specific RDS database cluster identified by its cluster ID, including configuration, endpoints, backup settings, and maintenance windows.
"""

# Data Models


class ClusterResponse(BaseModel):
    """DB cluster response model."""

    cluster: DBClusterTypeDef = Field(..., description='The raw cluster data from AWS')
    resource_uri: Optional[str] = Field(None, description='The resource URI for this cluster')

    @classmethod
    def from_DBClusterTypeDef(cls, cluster: DBClusterTypeDef) -> 'ClusterResponse':
        """Takes raw cluster data from AWS and formats it into a structured ClusterResponse model.

        Args:
            cluster: Raw cluster data from AWS

        Returns:
            ClusterResponse: Formatted cluster information with comprehensive details
        """
        return cls(
            cluster=cluster,
            resource_uri=f'aws-rds://db-cluster/{cluster.get("DBClusterIdentifier")}',
        )


resource_params = {
    'uri': 'aws-rds://db-cluster/{cluster_id}',
    'name': 'DescribeDBClusterDetail',
    'description': DESCRIBE_CLUSTER_DETAIL_RESOURCE_DESCRIPTION,
    'mime_type': 'application/json',
}

tool_params = {
    'name': 'DescribeRDSDBClusterDetail',
    'description': DESCRIBE_CLUSTER_DETAIL_RESOURCE_DESCRIPTION,
}


@register_mcp_primitive_by_context(resource_params, tool_params)
@handle_exceptions
async def describe_cluster_detail(
    cluster_id: str = Field(
        ..., description='The unique identifier of the RDS DB cluster to retrieve details for'
    ),
) -> ClusterResponse:
    """Get detailed information about a specific cluster as a resource.

    Args:
        cluster_id: The unique identifier of the RDS cluster

    Returns:
        ClusterResponse: Detailed information about the specified RDS cluster

    Raises:
        ValueError: If the specified cluster is not found
    """
    logger.info(f'Getting cluster detail resource for {cluster_id}')
    rds_client = RDSConnectionManager.get_connection()
    response = await asyncio.to_thread(
        rds_client.describe_db_clusters, DBClusterIdentifier=cluster_id
    )

    clusters = response.get('DBClusters', [])
    if not clusters:
        raise ValueError(f'Cluster {cluster_id} not found')
    response = ClusterResponse.from_DBClusterTypeDef(clusters[0])

    return response
