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

"""Tests for RDS cluster discovery functionality."""

import pytest
from awslabs.rds_monitoring_mcp_server.resources.db_cluster.cluster_discovery import (
    ClusterDetails,
    ClusterOverview,
    get_cluster_details,
    get_cluster_overview,
    list_clusters,
)
from datetime import datetime
from unittest.mock import MagicMock, patch


# Common test data
MOCK_DB_CLUSTER = {
    'DBClusterIdentifier': 'test-cluster',
    'DbClusterResourceId': 'cluster-abc123',
    'DBClusterArn': 'arn:aws:rds:us-west-2:123456789012:cluster:test-cluster',
    'Status': 'available',
    'Engine': 'aurora-mysql',
    'EngineVersion': '5.7.mysql_aurora.2.10.2',
    'AvailabilityZones': ['us-west-2a', 'us-west-2b', 'us-west-2c'],
    'MultiAZ': True,
    'TagList': [
        {'Key': 'Environment', 'Value': 'test'},
        {'Key': 'Project', 'Value': 'rds-monitoring'},
    ],
    'DatabaseName': 'testdb',
    'DBClusterParameterGroup': 'default.aurora-mysql5.7',
    'DBSubnetGroup': 'default-vpc-abc123',
    'VpcSecurityGroups': [
        {'VpcSecurityGroupId': 'sg-12345', 'Status': 'active'},
        {'VpcSecurityGroupId': 'sg-67890', 'Status': 'active'},
    ],
    'StorageEncrypted': True,
    'KmsKeyId': 'arn:aws:kms:us-west-2:123456789012:key/abcd1234-5678-90ab-cdef-example11111',
    'ClusterCreateTime': datetime(2023, 1, 1, 12, 0, 0),
    'BackupRetentionPeriod': 7,
    'PreferredBackupWindow': '07:00-09:00',
    'PreferredMaintenanceWindow': 'sun:09:00-sun:10:00',
    'DBClusterMembers': [
        {
            'DBInstanceIdentifier': 'test-cluster-instance-1',
            'IsClusterWriter': True,
            'DBClusterParameterGroupStatus': 'in-sync',
            'PromotionTier': 1,
        },
        {
            'DBInstanceIdentifier': 'test-cluster-instance-2',
            'IsClusterWriter': False,
            'DBClusterParameterGroupStatus': 'in-sync',
            'PromotionTier': 2,
        },
    ],
}

MOCK_DB_CLUSTERS_RESPONSE = {'DBClusters': [MOCK_DB_CLUSTER]}


class TestGetClusterOverview:
    """Tests for the get_cluster_overview helper function."""

    def test_standard_cluster_data(self):
        """Test with standard cluster data containing all fields."""
        result = get_cluster_overview(MOCK_DB_CLUSTER)

        assert isinstance(result, ClusterOverview)
        assert result.db_cluster_identifier == 'test-cluster'
        assert result.db_cluster_resource_id == 'cluster-abc123'
        assert result.db_cluster_arn == 'arn:aws:rds:us-west-2:123456789012:cluster:test-cluster'
        assert result.status == 'available'
        assert result.engine == 'aurora-mysql'
        assert result.engine_version == '5.7.mysql_aurora.2.10.2'
        assert result.availability_zones == ['us-west-2a', 'us-west-2b', 'us-west-2c']
        assert result.multi_az is True
        assert len(result.tag_list) == 2
        assert result.tag_list[0]['Key'] == 'Environment'
        assert result.tag_list[0]['Value'] == 'test'

    def test_with_minimal_data(self):
        """Test with minimal required fields in cluster data."""
        minimal_cluster = {
            'DBClusterIdentifier': 'minimal-cluster',
            'DbClusterResourceId': 'minimal-abc123',
            'DBClusterArn': 'arn:aws:rds:us-west-2:123456789012:cluster:minimal-cluster',
            'Status': 'available',
            'Engine': 'aurora-mysql',
            'EngineVersion': '5.7',
            'MultiAZ': False,
        }

        result = get_cluster_overview(minimal_cluster)

        assert isinstance(result, ClusterOverview)
        assert result.db_cluster_identifier == 'minimal-cluster'
        assert result.db_cluster_resource_id == 'minimal-abc123'
        assert result.availability_zones is None
        assert result.tag_list is None


class TestListClusters:
    """Tests for the list_clusters MCP resource."""

    @pytest.mark.asyncio
    @patch(
        'awslabs.rds_monitoring_mcp_server.resources.db_cluster.cluster_discovery.RDSConnectionManager'
    )
    async def test_standard_response(self, mock_connection_manager):
        """Test with standard response containing clusters."""
        mock_rds_client = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator_iterator = MagicMock()

        mock_connection_manager.get_connection.return_value = mock_rds_client
        mock_rds_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = mock_paginator_iterator
        mock_paginator_iterator.__iter__.return_value = [MOCK_DB_CLUSTERS_RESPONSE]

        result = await list_clusters()

        mock_connection_manager.get_connection.assert_called_once()
        mock_rds_client.get_paginator.assert_called_once_with('describe_db_clusters')

        assert len(result) == 1
        assert isinstance(result[0], ClusterOverview)
        assert result[0].db_cluster_identifier == 'test-cluster'
        assert result[0].engine == 'aurora-mysql'
        assert result[0].multi_az is True

    @pytest.mark.asyncio
    @patch(
        'awslabs.rds_monitoring_mcp_server.resources.db_cluster.cluster_discovery.RDSConnectionManager'
    )
    async def test_empty_response(self, mock_connection_manager):
        """Test with empty response containing no clusters."""
        mock_rds_client = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator_iterator = MagicMock()

        mock_connection_manager.get_connection.return_value = mock_rds_client
        mock_rds_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = mock_paginator_iterator
        mock_paginator_iterator.__iter__.return_value = [{'DBClusters': []}]

        result = await list_clusters()

        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.asyncio
    @patch(
        'awslabs.rds_monitoring_mcp_server.resources.db_cluster.cluster_discovery.RDSConnectionManager'
    )
    async def test_with_empty_tags(self, mock_connection_manager):
        """Test with clusters having empty tag lists."""
        mock_cluster = dict(MOCK_DB_CLUSTER)
        mock_cluster['TagList'] = []

        mock_rds_client = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator_iterator = MagicMock()

        mock_connection_manager.get_connection.return_value = mock_rds_client
        mock_rds_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = mock_paginator_iterator
        mock_paginator_iterator.__iter__.return_value = [{'DBClusters': [mock_cluster]}]

        result = await list_clusters()

        assert len(result) == 1
        assert result[0].tag_list is None


class TestGetClusterDetails:
    """Tests for the get_cluster_details MCP resource."""

    @pytest.mark.asyncio
    @patch(
        'awslabs.rds_monitoring_mcp_server.resources.db_cluster.cluster_discovery.RDSConnectionManager'
    )
    async def test_standard_response(self, mock_connection_manager):
        """Test with standard response containing all cluster details."""
        mock_rds_client = MagicMock()
        mock_connection_manager.get_connection.return_value = mock_rds_client
        mock_rds_client.describe_db_clusters.return_value = MOCK_DB_CLUSTERS_RESPONSE

        result = await get_cluster_details('test-cluster')

        mock_connection_manager.get_connection.assert_called_once()
        mock_rds_client.describe_db_clusters.assert_called_once_with(
            DBClusterIdentifier='test-cluster'
        )

        assert isinstance(result, ClusterDetails)

        # Core attributes
        assert result.cluster_overview.db_cluster_identifier == 'test-cluster'
        assert result.cluster_overview.engine == 'aurora-mysql'
        assert result.cluster_overview.multi_az is True

        # Configuration details
        assert result.database_name == 'testdb'
        assert result.db_cluster_parameter_group == 'default.aurora-mysql5.7'
        assert result.db_subnet_group == 'default-vpc-abc123'
        assert result.backup_retention_period == 7
        assert result.preferred_backup_window == '07:00-09:00'
        assert result.preferred_maintenance_window == 'sun:09:00-sun:10:00'
        assert result.storage_encrypted is True
        assert (
            result.kms_key_id
            == 'arn:aws:kms:us-west-2:123456789012:key/abcd1234-5678-90ab-cdef-example11111'
        )

        # Nested structures
        assert len(result.vpc_security_groups) == 2
        assert result.vpc_security_groups[0]['vpc_security_group_id'] == 'sg-12345'
        assert result.vpc_security_groups[0]['status'] == 'active'

        assert len(result.db_cluster_members) == 2
        assert result.db_cluster_members[0]['db_instance_identifier'] == 'test-cluster-instance-1'
        assert result.db_cluster_members[0]['is_cluster_writer'] is True

    @pytest.mark.asyncio
    @patch(
        'awslabs.rds_monitoring_mcp_server.resources.db_cluster.cluster_discovery.RDSConnectionManager'
    )
    async def test_error_handling(self, mock_connection_manager):
        """Test exception propagation when cluster is not found."""
        mock_rds_client = MagicMock()
        mock_connection_manager.get_connection.return_value = mock_rds_client
        mock_rds_client.describe_db_clusters.side_effect = Exception('Cluster not found')

        with pytest.raises(Exception) as excinfo:
            await get_cluster_details('non-existent-cluster')

        assert 'Cluster not found' in str(excinfo.value)

    @pytest.mark.asyncio
    @patch(
        'awslabs.rds_monitoring_mcp_server.resources.db_cluster.cluster_discovery.RDSConnectionManager'
    )
    async def test_datetime_handling(self, mock_connection_manager):
        """Test proper conversion of datetime objects in response."""
        test_datetime = datetime(2023, 1, 1, 12, 0, 0)
        mock_cluster = dict(MOCK_DB_CLUSTER)
        mock_cluster['ClusterCreateTime'] = test_datetime
        mock_cluster['EarliestRestorableTime'] = test_datetime
        mock_cluster['LatestRestorableTime'] = test_datetime

        mock_rds_client = MagicMock()
        mock_connection_manager.get_connection.return_value = mock_rds_client
        mock_rds_client.describe_db_clusters.return_value = {'DBClusters': [mock_cluster]}

        result = await get_cluster_details('test-cluster')

        assert result.cluster_create_time == str(test_datetime)
        assert result.earliest_restorable_time == str(test_datetime)
        assert result.latest_restorable_time == str(test_datetime)
