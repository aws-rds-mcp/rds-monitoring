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

"""Tests for the server module of the rds-monitoring-mcp-server."""

import pytest
from awslabs.rds_monitoring_mcp_server.models import (
    ClusterOverview,
    InstanceOverview,
)
from awslabs.rds_monitoring_mcp_server.server import (
    list_clusters_resource,
    list_instances_resource,
    mcp,
)
from unittest.mock import patch


class TestMCPServer:
    """Tests for the MCP server."""

    def test_mcp_initialization(self):
        """Test that the MCP server is initialized correctly."""
        assert mcp.name == 'RDS Monitoring'
        assert mcp.instructions is not None
        assert 'AWS Labs RDS Control Plane Operations MCP Server' in mcp.instructions
        assert 'boto3' in mcp.dependencies
        assert 'pydantic' in mcp.dependencies
        assert 'loguru' in mcp.dependencies


class TestListInstancesResource:
    """Tests for the list_instances_resource function."""

    @pytest.mark.asyncio
    @patch('awslabs.rds_monitoring_mcp_server.server.list_instances')
    async def test_list_instances_resource(self, mock_list_instances):
        """Test the list_instances_resource function."""
        mock_instances = [
            InstanceOverview(
                db_instance_identifier='db-instance-1',
                dbi_resource_id='db-resource-1',
                db_instance_arn='arn:aws:rds:us-west-2:123456789012:db:db-instance-1',
                db_instance_status='available',
                db_instance_class='db.t3.medium',
                engine='mysql',
                availability_zone='us-west-2a',
                multi_az=False,
                tag_list=[{'Key': 'Environment', 'Value': 'Test'}],
            ),
            InstanceOverview(
                db_instance_identifier='db-instance-2',
                dbi_resource_id='db-resource-2',
                db_instance_arn='arn:aws:rds:us-west-2:123456789012:db:db-instance-2',
                db_instance_status='available',
                db_instance_class='db.t3.large',
                engine='postgres',
                availability_zone='us-west-2b',
                multi_az=True,
                tag_list=[{'Key': 'Environment', 'Value': 'Production'}],
            ),
        ]
        mock_list_instances.return_value = mock_instances

        result = await list_instances_resource()

        assert len(result) == 2
        assert result[0].db_instance_identifier == 'db-instance-1'
        assert result[0].dbi_resource_id == 'db-resource-1'
        assert result[0].engine == 'mysql'
        assert result[1].db_instance_identifier == 'db-instance-2'
        assert result[1].dbi_resource_id == 'db-resource-2'
        assert result[1].engine == 'postgres'

        mock_list_instances.assert_called_once()


class TestListClustersResource:
    """Tests for the list_clusters_resource function."""

    @pytest.mark.asyncio
    @patch('awslabs.rds_monitoring_mcp_server.server.list_clusters')
    async def test_list_clusters_resource(self, mock_list_clusters):
        """Test the list_clusters_resource function."""
        mock_clusters = [
            ClusterOverview(
                db_cluster_identifier='db-cluster-1',
                db_cluster_resource_id='cluster-resource-1',
                db_cluster_arn='arn:aws:rds:us-west-2:123456789012:cluster:db-cluster-1',
                status='available',
                engine='aurora-mysql',
                engine_version='5.7.mysql_aurora.2.11.1',
                availability_zones=['us-west-2a', 'us-west-2b', 'us-west-2c'],
                multi_az=True,
                tag_list=[{'Key': 'Environment', 'Value': 'Test'}],
            ),
            ClusterOverview(
                db_cluster_identifier='db-cluster-2',
                db_cluster_resource_id='cluster-resource-2',
                db_cluster_arn='arn:aws:rds:us-west-2:123456789012:cluster:db-cluster-2',
                status='available',
                engine='aurora-postgresql',
                engine_version='13.7.postgresql',
                availability_zones=['us-west-2a', 'us-west-2b'],
                multi_az=True,
                tag_list=[{'Key': 'Environment', 'Value': 'Production'}],
            ),
        ]
        mock_list_clusters.return_value = mock_clusters

        result = await list_clusters_resource()

        assert len(result) == 2
        assert result[0].db_cluster_identifier == 'db-cluster-1'
        assert result[0].db_cluster_resource_id == 'cluster-resource-1'
        assert result[0].engine == 'aurora-mysql'
        assert result[1].db_cluster_identifier == 'db-cluster-2'
        assert result[1].db_cluster_resource_id == 'cluster-resource-2'
        assert result[1].engine == 'aurora-postgresql'

        mock_list_clusters.assert_called_once()
