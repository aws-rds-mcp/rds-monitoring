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
    ClusterDetails,
    ClusterOverview,
    InstanceDetails,
    InstanceOverview,
)
from awslabs.rds_monitoring_mcp_server.server import (
    cluster_details_resource,
    instance_details_resource,
    list_clusters_resource,
    list_instances_resource,
    mcp,
)
from unittest.mock import ANY, patch


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


class TestInstanceDetailsResource:
    """Tests for the instance_details_resource function."""

    @pytest.mark.asyncio
    @patch('awslabs.rds_monitoring_mcp_server.server.get_instance_details')
    async def test_instance_details_resource(self, mock_get_instance_details):
        """Test the instance_details_resource function."""
        instance_overview = InstanceOverview(
            db_instance_identifier='db-instance-1',
            dbi_resource_id='db-resource-1',
            db_instance_arn='arn:aws:rds:us-west-2:123456789012:db:db-instance-1',
            db_instance_status='available',
            db_instance_class='db.t3.medium',
            engine='mysql',
            availability_zone='us-west-2a',
            multi_az=False,
            tag_list=[{'Key': 'Environment', 'Value': 'Test'}],
        )

        mock_instance_details = InstanceDetails(
            instance_overview=instance_overview,
            allocated_storage=20,
            storage_type='gp2',
            storage_encrypted=True,
            engine_version='8.0.28',
            vpc_id='vpc-12345',
            publicly_accessible=False,
            backup_retention_period=7,
            db_parameter_groups=[{'name': 'default.mysql8.0', 'status': 'in-sync'}],
        )
        mock_get_instance_details.return_value = mock_instance_details

        result = await instance_details_resource(db_instance_identifier='db-instance-1')

        assert result.instance_overview.db_instance_identifier == 'db-instance-1'
        assert result.instance_overview.dbi_resource_id == 'db-resource-1'
        assert result.instance_overview.engine == 'mysql'
        assert result.allocated_storage == 20
        assert result.storage_type == 'gp2'
        assert result.storage_encrypted is True
        assert result.engine_version == '8.0.28'
        assert result.vpc_id == 'vpc-12345'
        assert result.publicly_accessible is False
        assert result.backup_retention_period == 7
        assert result.db_parameter_groups[0]['name'] == 'default.mysql8.0'

        mock_get_instance_details.assert_called_once_with(
            rds_client=ANY, db_instance_identifier='db-instance-1'
        )


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


class TestClusterDetailsResource:
    """Tests for the cluster_details_resource function."""

    @pytest.mark.asyncio
    @patch('awslabs.rds_monitoring_mcp_server.server.get_cluster_details')
    async def test_cluster_details_resource(self, mock_get_cluster_details):
        """Test the cluster_details_resource function."""
        cluster_overview = ClusterOverview(
            db_cluster_identifier='db-cluster-1',
            db_cluster_resource_id='cluster-resource-1',
            db_cluster_arn='arn:aws:rds:us-west-2:123456789012:cluster:db-cluster-1',
            status='available',
            engine='aurora-mysql',
            engine_version='5.7.mysql_aurora.2.11.1',
            availability_zones=['us-west-2a', 'us-west-2b', 'us-west-2c'],
            multi_az=True,
            tag_list=[{'Key': 'Environment', 'Value': 'Test'}],
        )

        mock_cluster_details = ClusterDetails(
            cluster_overview=cluster_overview,
            allocated_storage=100,
            storage_encrypted=True,
            database_name='testdb',
            db_cluster_parameter_group='default.aurora-mysql5.7',
            vpc_security_groups=[{'vpc_security_group_id': 'sg-12345', 'status': 'active'}],
            backup_retention_period=7,
            db_cluster_members=[
                {
                    'db_instance_identifier': 'db-instance-1',
                    'is_cluster_writer': True,
                    'db_cluster_parameter_group_status': 'in-sync',
                    'promotion_tier': 1,
                },
                {
                    'db_instance_identifier': 'db-instance-2',
                    'is_cluster_writer': False,
                    'db_cluster_parameter_group_status': 'in-sync',
                    'promotion_tier': 2,
                },
            ],
            engine_mode='provisioned',
            deletion_protection=True,
        )
        mock_get_cluster_details.return_value = mock_cluster_details

        result = await cluster_details_resource(db_cluster_identifier='db-cluster-1')

        assert result.cluster_overview.db_cluster_identifier == 'db-cluster-1'
        assert result.cluster_overview.db_cluster_resource_id == 'cluster-resource-1'
        assert result.cluster_overview.engine == 'aurora-mysql'
        assert result.allocated_storage == 100
        assert result.storage_encrypted is True
        assert result.database_name == 'testdb'
        assert result.db_cluster_parameter_group == 'default.aurora-mysql5.7'
        assert result.vpc_security_groups[0]['vpc_security_group_id'] == 'sg-12345'
        assert result.backup_retention_period == 7
        assert len(result.db_cluster_members) == 2
        assert result.db_cluster_members[0]['db_instance_identifier'] == 'db-instance-1'
        assert result.db_cluster_members[0]['is_cluster_writer'] is True
        assert result.engine_mode == 'provisioned'
        assert result.deletion_protection is True

        mock_get_cluster_details.assert_called_once_with(
            rds_client=ANY, cluster_identifier='db-cluster-1'
        )


class TestServerIntegration:
    """Integration tests for the server module."""

    @pytest.mark.asyncio
    @patch('awslabs.rds_monitoring_mcp_server.server.list_instances')
    @patch('awslabs.rds_monitoring_mcp_server.server.get_instance_details')
    @patch('awslabs.rds_monitoring_mcp_server.server.list_clusters')
    @patch('awslabs.rds_monitoring_mcp_server.server.get_cluster_details')
    async def test_server_integration(
        self,
        mock_get_cluster_details,
        mock_list_clusters,
        mock_get_instance_details,
        mock_list_instances,
    ):
        """Test the server integration."""
        instance_overview = InstanceOverview(
            db_instance_identifier='test-instance',
            dbi_resource_id='db-resource-id',
            db_instance_arn='arn:aws:rds:us-west-2:123456789012:db:test-instance',
            db_instance_status='available',
            db_instance_class='db.t3.medium',
            engine='mysql',
            availability_zone='us-west-2a',
            multi_az=False,
            tag_list=[{'Key': 'Environment', 'Value': 'Test'}],
        )

        mock_instance_details = InstanceDetails(
            instance_overview=instance_overview,
            allocated_storage=20,
            storage_type='gp2',
            storage_encrypted=True,
            engine_version='8.0.28',
        )

        mock_list_instances.return_value = [instance_overview]
        mock_get_instance_details.return_value = mock_instance_details

        cluster_overview = ClusterOverview(
            db_cluster_identifier='test-cluster',
            db_cluster_resource_id='cluster-resource-id',
            db_cluster_arn='arn:aws:rds:us-west-2:123456789012:cluster:test-cluster',
            status='available',
            engine='aurora-mysql',
            engine_version='5.7.mysql_aurora.2.11.1',
            availability_zones=['us-west-2a', 'us-west-2b'],
            multi_az=True,
            tag_list=[{'Key': 'Environment', 'Value': 'Test'}],
        )

        mock_cluster_details = ClusterDetails(
            cluster_overview=cluster_overview,
            allocated_storage=100,
            storage_encrypted=True,
            database_name='testdb',
        )

        mock_list_clusters.return_value = [cluster_overview]
        mock_get_cluster_details.return_value = mock_cluster_details

        instances_result = await list_instances_resource()
        assert len(instances_result) == 1
        assert instances_result[0].db_instance_identifier == 'test-instance'

        instance_detail_result = await instance_details_resource('test-instance')
        assert instance_detail_result.instance_overview.db_instance_identifier == 'test-instance'
        assert instance_detail_result.allocated_storage == 20

        clusters_result = await list_clusters_resource()
        assert len(clusters_result) == 1
        assert clusters_result[0].db_cluster_identifier == 'test-cluster'

        cluster_detail_result = await cluster_details_resource('test-cluster')
        assert cluster_detail_result.cluster_overview.db_cluster_identifier == 'test-cluster'
        assert cluster_detail_result.allocated_storage == 100

        mock_list_instances.assert_called_once()
        mock_get_instance_details.assert_called_once_with(
            rds_client=ANY, db_instance_identifier='test-instance'
        )
        mock_list_clusters.assert_called_once()
        mock_get_cluster_details.assert_called_once_with(
            rds_client=ANY, cluster_identifier='test-cluster'
        )
