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

"""Tests for RDS instance discovery functionality."""

import pytest
from awslabs.rds_monitoring_mcp_server.resources.db_instance.instance_discovery import (
    InstanceDetails,
    InstanceOverview,
    get_instance_details,
    get_instance_overview,
    list_instances,
)
from datetime import datetime
from unittest.mock import MagicMock


# Common test data
MOCK_DB_INSTANCE = {
    'DBInstanceIdentifier': 'test-instance',
    'DbiResourceId': 'db-ABC123DEF456GHI',
    'DBInstanceArn': 'arn:aws:rds:us-west-2:123456789012:db:test-instance',
    'DBInstanceStatus': 'available',
    'DBInstanceClass': 'db.t3.medium',
    'Engine': 'mysql',
    'EngineVersion': '8.0.28',
    'MultiAZ': False,
    'AvailabilityZone': 'us-west-2a',
    'TagList': [
        {'Key': 'Environment', 'Value': 'test'},
        {'Key': 'Project', 'Value': 'rds-monitoring'},
    ],
    'DBName': 'testdb',
    'StorageType': 'gp2',
    'AllocatedStorage': 20,
    'StorageEncrypted': True,
    'KmsKeyId': 'arn:aws:kms:us-west-2:123456789012:key/abcd1234-5678-90ab-cdef-example11111',
    'PubliclyAccessible': False,
    'VpcSecurityGroups': [
        {'VpcSecurityGroupId': 'sg-12345', 'Status': 'active'},
        {'VpcSecurityGroupId': 'sg-67890', 'Status': 'active'},
    ],
    'DBSubnetGroup': {
        'DBSubnetGroupName': 'default-vpc-abc123',
        'VpcId': 'vpc-abc123',
    },
    'InstanceCreateTime': datetime(2023, 1, 1, 12, 0, 0),
    'BackupRetentionPeriod': 7,
    'PreferredBackupWindow': '07:00-09:00',
    'PreferredMaintenanceWindow': 'sun:09:00-sun:10:00',
    'AutoMinorVersionUpgrade': True,
    'CopyTagsToSnapshot': True,
    'DBParameterGroups': [
        {'DBParameterGroupName': 'default.mysql8.0', 'ParameterApplyStatus': 'in-sync'}
    ],
    'ReadReplicaSourceDBInstanceIdentifier': None,
    'ReadReplicaDBInstanceIdentifiers': [],
    'NetworkType': 'IPV4',
    'PerformanceInsightsEnabled': False,
}

MOCK_DB_INSTANCES_RESPONSE = {'DBInstances': [MOCK_DB_INSTANCE]}


class TestGetInstanceOverview:
    """Tests for the get_instance_overview helper function."""

    def test_standard_instance_data(self):
        """Test with standard instance data containing all fields."""
        result = get_instance_overview(MOCK_DB_INSTANCE)

        assert isinstance(result, InstanceOverview)
        assert result.db_instance_identifier == 'test-instance'
        assert result.dbi_resource_id == 'db-ABC123DEF456GHI'
        assert result.db_instance_arn == 'arn:aws:rds:us-west-2:123456789012:db:test-instance'
        assert result.db_instance_status == 'available'
        assert result.db_instance_class == 'db.t3.medium'
        assert result.engine == 'mysql'
        assert result.availability_zone == 'us-west-2a'
        assert result.multi_az is False
        assert len(result.tag_list) == 2
        assert result.tag_list[0]['Key'] == 'Environment'
        assert result.tag_list[0]['Value'] == 'test'

    def test_with_minimal_data(self):
        """Test with minimal required fields in instance data."""
        minimal_instance = {
            'DBInstanceIdentifier': 'minimal-instance',
            'DbiResourceId': 'db-MINIMALXYZ',
            'DBInstanceArn': 'arn:aws:rds:us-west-2:123456789012:db:minimal-instance',
            'DBInstanceStatus': 'available',
            'DBInstanceClass': 'db.t3.micro',
            'Engine': 'mysql',
            'MultiAZ': False,
        }

        result = get_instance_overview(minimal_instance)

        assert isinstance(result, InstanceOverview)
        assert result.db_instance_identifier == 'minimal-instance'
        assert result.dbi_resource_id == 'db-MINIMALXYZ'
        assert result.db_instance_arn == 'arn:aws:rds:us-west-2:123456789012:db:minimal-instance'
        assert result.db_instance_status == 'available'
        assert result.db_instance_class == 'db.t3.micro'
        assert result.engine == 'mysql'
        assert result.availability_zone is None
        assert result.multi_az is False
        assert result.tag_list is None


class TestListInstances:
    """Tests for the list_instances MCP resource."""

    @pytest.mark.asyncio
    async def test_standard_response(self, mock_rds_client):
        """Test with standard response containing instances."""
        mock_paginator = MagicMock()
        mock_paginator_iterator = MagicMock()

        mock_rds_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = mock_paginator_iterator
        mock_paginator_iterator.__iter__.return_value = [MOCK_DB_INSTANCES_RESPONSE]

        result = await list_instances()

        mock_rds_client.get_paginator.assert_called_once_with('describe_db_instances')

        assert len(result) == 1
        assert isinstance(result[0], InstanceOverview)
        assert result[0].db_instance_identifier == 'test-instance'
        assert result[0].engine == 'mysql'
        assert result[0].db_instance_class == 'db.t3.medium'

    @pytest.mark.asyncio
    async def test_empty_response(self, mock_rds_client):
        """Test with empty response containing no instances."""
        mock_paginator = MagicMock()
        mock_paginator_iterator = MagicMock()

        mock_rds_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = mock_paginator_iterator
        mock_paginator_iterator.__iter__.return_value = [{'DBInstances': []}]

        result = await list_instances()

        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_with_empty_tags(self, mock_rds_client):
        """Test with instances having empty tag lists."""
        mock_instance = dict(MOCK_DB_INSTANCE)
        mock_instance['TagList'] = []

        mock_paginator = MagicMock()
        mock_paginator_iterator = MagicMock()

        mock_rds_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = mock_paginator_iterator
        mock_paginator_iterator.__iter__.return_value = [{'DBInstances': [mock_instance]}]

        result = await list_instances()

        assert len(result) == 1
        assert result[0].tag_list == []


class TestGetInstanceDetails:
    """Tests for the get_instance_details MCP resource."""

    @pytest.mark.asyncio
    async def test_standard_response(self, mock_rds_client):
        """Test with standard response containing all instance details."""
        mock_rds_client.describe_db_instances.return_value = MOCK_DB_INSTANCES_RESPONSE

        result = await get_instance_details('test-instance')

        mock_rds_client.describe_db_instances.assert_called_once_with(
            DBInstanceIdentifier='test-instance'
        )

        assert isinstance(result, InstanceDetails)

        assert result.instance_overview.db_instance_identifier == 'test-instance'
        assert result.instance_overview.engine == 'mysql'
        assert result.instance_overview.db_instance_class == 'db.t3.medium'

        assert result.allocated_storage == 20
        assert result.storage_type == 'gp2'
        assert result.storage_encrypted is True

        assert result.db_name == 'testdb'
        assert result.engine_version == '8.0.28'

        assert result.vpc_id == 'vpc-abc123'
        assert result.publicly_accessible is False
        assert result.db_subnet_group_name == 'default-vpc-abc123'
        assert result.network_type == 'IPV4'

        assert result.backup_retention_period == 7
        assert result.preferred_backup_window == '07:00-09:00'
        assert result.preferred_maintenance_window == 'sun:09:00-sun:10:00'
        assert result.auto_minor_version_upgrade is True
        assert result.copy_tags_to_snapshot is True

        assert len(result.db_parameter_groups) == 1
        assert result.db_parameter_groups[0]['name'] == 'default.mysql8.0'
        assert result.db_parameter_groups[0]['status'] == 'in-sync'

        assert len(result.vpc_security_groups) == 2
        assert result.vpc_security_groups[0]['vpc_security_group_id'] == 'sg-12345'
        assert result.vpc_security_groups[0]['status'] == 'active'

        assert result.read_replica_source_db_instance_identifier is None
        assert result.read_replica_db_instance_identifiers == []

    @pytest.mark.asyncio
    async def test_error_handling(self, mock_rds_client):
        """Test exception propagation when instance is not found."""
        mock_rds_client.describe_db_instances.side_effect = Exception('Instance not found')

        with pytest.raises(Exception) as excinfo:
            await get_instance_details('non-existent-instance')

        assert 'Instance not found' in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_datetime_handling(self, mock_rds_client):
        """Test proper conversion of datetime objects in response."""
        test_datetime = datetime(2023, 1, 1, 12, 0, 0)
        mock_instance = dict(MOCK_DB_INSTANCE)
        mock_instance['InstanceCreateTime'] = test_datetime
        mock_instance['LatestRestorableTime'] = test_datetime

        mock_rds_client.describe_db_instances.return_value = {'DBInstances': [mock_instance]}

        result = await get_instance_details('test-instance')

        assert result.instance_create_time == str(test_datetime)
        assert result.latest_restorable_time == str(test_datetime)

    @pytest.mark.asyncio
    async def test_read_replica_configuration(self, mock_rds_client):
        """Test handling of read replica configuration."""
        mock_instance = dict(MOCK_DB_INSTANCE)
        mock_instance['ReadReplicaSourceDBInstanceIdentifier'] = 'source-instance'
        mock_instance['ReadReplicaDBInstanceIdentifiers'] = ['replica-1', 'replica-2']

        mock_rds_client.describe_db_instances.return_value = {'DBInstances': [mock_instance]}

        result = await get_instance_details('test-instance')

        assert result.read_replica_source_db_instance_identifier == 'source-instance'
        assert len(result.read_replica_db_instance_identifiers) == 2
        assert 'replica-1' in result.read_replica_db_instance_identifiers
        assert 'replica-2' in result.read_replica_db_instance_identifiers
