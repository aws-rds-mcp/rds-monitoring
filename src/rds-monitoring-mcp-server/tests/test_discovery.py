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

"""Tests for the discovery module of the rds-monitoring-mcp-server."""

import pytest
from awslabs.rds_monitoring_mcp_server.discovery import (
    get_cluster_details,
    get_cluster_overview,
    get_instance_details,
    get_instance_overview,
    list_clusters,
    list_instances,
)
from awslabs.rds_monitoring_mcp_server.models import (
    ClusterDetails,
    ClusterOverview,
    InstanceDetails,
    InstanceOverview,
)
from tests.test_constants import MOCK_DB_CLUSTERS_RESPONSE, MOCK_DB_INSTANCES_RESPONSE
from unittest.mock import MagicMock, patch


class TestGetInstanceOverview:
    """Tests for the get_instance_overview function."""

    def test_get_instance_overview_complete(self):
        """Test extracting instance overview with complete data."""
        mock_instance = MOCK_DB_INSTANCES_RESPONSE['DBInstances'][0]

        result = get_instance_overview(mock_instance)

        assert isinstance(result, InstanceOverview)
        assert result.db_instance_identifier == 'example-postgres-instance'
        assert result.dbi_resource_id == 'db-EXAMPLE1234567890ABCDEFG'
        assert result.db_instance_status == 'available'
        assert result.db_instance_class == 'db.r6g.large'
        assert result.engine == 'aurora-postgresql'
        assert result.availability_zone == 'us-east-1a'
        assert result.multi_az is False
        assert len(result.tag_list) == 0


class TestGetClusterOverview:
    """Tests for the get_cluster_overview function."""

    def test_get_cluster_overview_complete(self):
        """Test extracting cluster overview with complete data."""
        mock_cluster = MOCK_DB_CLUSTERS_RESPONSE['DBClusters'][0]

        result = get_cluster_overview(mock_cluster)

        assert isinstance(result, ClusterOverview)
        assert result.db_cluster_identifier == 'example-postgres-cluster'
        assert result.db_cluster_resource_id == 'cluster-ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        assert result.status == 'available'
        assert result.engine == 'aurora-postgresql'
        assert result.multi_az is False
        assert len(result.tag_list) == 0


class TestListInstances:
    """Tests for the list_instances function."""

    @pytest.mark.asyncio
    async def test_list_instances(self):
        """Test retrieving a list of RDS instances."""
        mock_rds_client = MagicMock()
        paginator = MagicMock()
        paginator.paginate.return_value = [MOCK_DB_INSTANCES_RESPONSE]
        mock_rds_client.get_paginator.return_value = paginator

        result = await list_instances(mock_rds_client)

        assert len(result) == 3
        assert isinstance(result[0], InstanceOverview)
        assert isinstance(result[1], InstanceOverview)
        assert isinstance(result[2], InstanceOverview)
        assert result[0].db_instance_identifier == 'example-postgres-instance'
        assert result[1].db_instance_identifier == 'example-mysql-db'
        assert result[2].db_instance_identifier == 'example-db-1'
        assert result[0].engine == 'aurora-postgresql'
        assert result[1].engine == 'mysql'
        assert result[2].engine == 'mysql'

        mock_rds_client.get_paginator.assert_called_once_with('describe_db_instances')
        paginator.paginate.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_instances_empty(self):
        """Test retrieving a list of RDS instances when none exist."""
        mock_rds_client = MagicMock()
        paginator = MagicMock()
        paginator.paginate.return_value = [{'DBInstances': []}]
        mock_rds_client.get_paginator.return_value = paginator

        result = await list_instances(mock_rds_client)

        assert len(result) == 0

        mock_rds_client.get_paginator.assert_called_once_with('describe_db_instances')
        paginator.paginate.assert_called_once()


class TestGetInstanceDetails:
    """Tests for the get_instance_details function."""

    @pytest.mark.asyncio
    async def test_get_instance_details(self):
        """Test retrieving detailed information about a specific RDS instance."""
        mock_rds_client = MagicMock()
        mock_rds_client.describe_db_instances.return_value = {
            'DBInstances': [MOCK_DB_INSTANCES_RESPONSE['DBInstances'][0]]
        }

        result = await get_instance_details(mock_rds_client, 'example-postgres-instance')

        assert isinstance(result, InstanceDetails)
        assert isinstance(result.instance_overview, InstanceOverview)
        assert result.instance_overview.db_instance_identifier == 'example-postgres-instance'
        assert result.allocated_storage == 1
        assert result.storage_type == 'aurora'
        assert result.storage_encrypted is False
        assert result.publicly_accessible is True
        assert len(result.vpc_security_groups) == 1
        assert result.vpc_security_groups[0]['vpc_security_group_id'] == 'sg-example12345678'
        assert len(result.db_parameter_groups) == 1
        assert result.db_parameter_groups[0]['name'] == 'default.aurora-postgresql16'

        mock_rds_client.describe_db_instances.assert_called_once_with(
            DBInstanceIdentifier='example-postgres-instance'
        )

    @pytest.mark.asyncio
    async def test_get_instance_details_not_found(self):
        """Test retrieving an instance that doesn't exist."""
        mock_rds_client = MagicMock()
        mock_rds_client.exceptions.DBInstanceNotFoundFault = Exception
        exception = mock_rds_client.exceptions.DBInstanceNotFoundFault(
            'Instance not found', 'Instance not found'
        )
        mock_rds_client.describe_db_instances.side_effect = exception

        with patch(
            'awslabs.rds_monitoring_mcp_server.discovery.handle_aws_error'
        ) as mock_handle_error:
            mock_handle_error.return_value = {'error': 'Instance not found'}
            await get_instance_details(mock_rds_client, 'nonexistent-instance')

            mock_handle_error.assert_called_once()
            args, _ = mock_handle_error.call_args
            assert 'describe_db_instances' in args[0]
            assert args[1] == exception

        mock_rds_client.describe_db_instances.assert_called_once_with(
            DBInstanceIdentifier='nonexistent-instance'
        )


class TestListClusters:
    """Tests for the list_clusters function."""

    @pytest.mark.asyncio
    async def test_list_clusters(self):
        """Test retrieving a list of RDS clusters."""
        mock_rds_client = MagicMock()
        paginator = MagicMock()
        paginator.paginate.return_value = [MOCK_DB_CLUSTERS_RESPONSE]
        mock_rds_client.get_paginator.return_value = paginator

        result = await list_clusters(mock_rds_client)

        assert len(result) == 1
        assert isinstance(result[0], ClusterOverview)
        assert result[0].db_cluster_identifier == 'example-postgres-cluster'
        assert result[0].db_cluster_resource_id == 'cluster-ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        assert result[0].status == 'available'
        assert result[0].engine == 'aurora-postgresql'
        assert result[0].multi_az is False

        mock_rds_client.get_paginator.assert_called_once_with('describe_db_clusters')
        paginator.paginate.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_clusters_empty(self):
        """Test retrieving a list of RDS clusters when none exist."""
        mock_rds_client = MagicMock()
        paginator = MagicMock()
        paginator.paginate.return_value = [{'DBClusters': []}]
        mock_rds_client.get_paginator.return_value = paginator

        result = await list_clusters(mock_rds_client)

        assert len(result) == 0

        mock_rds_client.get_paginator.assert_called_once_with('describe_db_clusters')
        paginator.paginate.assert_called_once()


class TestGetClusterDetails:
    """Tests for the get_cluster_details function."""

    @pytest.mark.asyncio
    async def test_get_cluster_details(self):
        """Test retrieving detailed information about a specific RDS cluster."""
        mock_rds_client = MagicMock()
        mock_rds_client.describe_db_clusters.return_value = {
            'DBClusters': [MOCK_DB_CLUSTERS_RESPONSE['DBClusters'][0]]
        }

        result = await get_cluster_details(mock_rds_client, 'example-postgres-cluster')

        assert isinstance(result, ClusterDetails)
        assert isinstance(result.cluster_overview, ClusterOverview)
        assert result.cluster_overview.db_cluster_identifier == 'example-postgres-cluster'
        assert (
            result.cluster_overview.db_cluster_resource_id == 'cluster-ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        )
        assert result.cluster_overview.status == 'available'
        assert result.cluster_overview.engine == 'aurora-postgresql'
        assert result.allocated_storage == 1
        assert len(result.vpc_security_groups) == 1
        assert result.vpc_security_groups[0]['vpc_security_group_id'] == 'sg-abcdefghij1234567'
        assert len(result.db_cluster_members) == 1
        assert (
            result.db_cluster_members[0]['db_instance_identifier'] == 'example-postgres-instance'
        )

        mock_rds_client.describe_db_clusters.assert_called_once_with(
            DBClusterIdentifier='example-postgres-cluster'
        )

    @pytest.mark.asyncio
    async def test_get_cluster_details_not_found(self):
        """Test retrieving a cluster that doesn't exist."""
        mock_rds_client = MagicMock()
        mock_rds_client.exceptions.DBClusterNotFoundFault = Exception
        exception = mock_rds_client.exceptions.DBClusterNotFoundFault(
            'Cluster not found', 'Cluster not found'
        )
        mock_rds_client.describe_db_clusters.side_effect = exception

        with patch(
            'awslabs.rds_monitoring_mcp_server.discovery.handle_aws_error'
        ) as mock_handle_error:
            mock_handle_error.return_value = {'error': 'Cluster not found'}
            await get_cluster_details(mock_rds_client, 'nonexistent-cluster')

            mock_handle_error.assert_called_once()
            args, _ = mock_handle_error.call_args
            assert 'describe_db_instances' in args[0]
            assert args[1] == exception

        mock_rds_client.describe_db_clusters.assert_called_once_with(
            DBClusterIdentifier='nonexistent-cluster'
        )
