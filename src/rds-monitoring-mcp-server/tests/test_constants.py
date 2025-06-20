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

"""Constants used by tests in the awslabs.rds-monitoring-mcp-server package."""

MOCK_DB_INSTANCES_RESPONSE = {
    'DBInstances': [
        {
            'DBInstanceIdentifier': 'example-postgres-instance',
            'DBInstanceClass': 'db.r6g.large',
            'Engine': 'aurora-postgresql',
            'DBInstanceStatus': 'available',
            'MasterUsername': 'postgres',
            'DBName': 'mydb',
            'Endpoint': {
                'Address': 'example-postgres-instance.example.us-east-1.rds.amazonaws.com',
                'Port': 5432,
                'HostedZoneId': 'EXAMPLE123456',
            },
            'AllocatedStorage': 1,
            'InstanceCreateTime': '2025-05-28T16:37:00.803000+00:00',
            'PreferredBackupWindow': '07:04-07:34',
            'BackupRetentionPeriod': 1,
            'DBSecurityGroups': [],
            'VpcSecurityGroups': [
                {'VpcSecurityGroupId': 'sg-example12345678', 'Status': 'active'}
            ],
            'DBParameterGroups': [
                {
                    'DBParameterGroupName': 'default.aurora-postgresql16',
                    'ParameterApplyStatus': 'in-sync',
                }
            ],
            'AvailabilityZone': 'us-east-1a',
            'PreferredMaintenanceWindow': 'fri:03:02-fri:03:32',
            'PendingModifiedValues': {},
            'MultiAZ': False,
            'EngineVersion': '16.6',
            'AutoMinorVersionUpgrade': True,
            'ReadReplicaDBInstanceIdentifiers': [],
            'LicenseModel': 'postgresql-license',
            'OptionGroupMemberships': [
                {'OptionGroupName': 'default:aurora-postgresql-16', 'Status': 'in-sync'}
            ],
            'PubliclyAccessible': True,
            'StorageType': 'aurora',
            'DbInstancePort': 0,
            'DBClusterIdentifier': 'example-postgres-cluster',
            'StorageEncrypted': False,
            'DbiResourceId': 'db-EXAMPLE1234567890ABCDEFG',
            'DomainMemberships': [],
            'CopyTagsToSnapshot': False,
            'MonitoringInterval': 0,
            'PromotionTier': 1,
            'DBInstanceArn': 'arn:aws:rds:us-east-1:123456789012:db:example-postgres-instance',
            'IAMDatabaseAuthenticationEnabled': False,
            'DatabaseInsightsMode': 'standard',
            'PerformanceInsightsEnabled': False,
            'DeletionProtection': False,
            'AssociatedRoles': [],
            'TagList': [],
            'CustomerOwnedIpEnabled': False,
            'BackupTarget': 'region',
            'NetworkType': 'IPV4',
            'StorageThroughput': 0,
            'DedicatedLogVolume': False,
            'EngineLifecycleSupport': 'open-source-rds-extended-support',
        },
        {
            'DBInstanceIdentifier': 'example-mysql-db',
            'DBInstanceClass': 'db.t3.micro',
            'Engine': 'mysql',
            'DBInstanceStatus': 'available',
            'MasterUsername': 'admin',
            'DBName': 'proddb',
            'Endpoint': {
                'Address': 'example-mysql-db.example.us-east-1.rds.amazonaws.com',
                'Port': 3306,
                'HostedZoneId': 'EXAMPLE123456',
            },
            'AllocatedStorage': 20,
            'InstanceCreateTime': '2025-06-16T18:43:42.793000+00:00',
            'PreferredBackupWindow': '07:52-08:22',
            'BackupRetentionPeriod': 7,
            'DBSecurityGroups': [],
            'VpcSecurityGroups': [
                {'VpcSecurityGroupId': 'sg-example12345678', 'Status': 'active'}
            ],
            'DBParameterGroups': [
                {'DBParameterGroupName': 'default.mysql8.0', 'ParameterApplyStatus': 'in-sync'}
            ],
            'AvailabilityZone': 'us-east-1f',
            'PreferredMaintenanceWindow': 'fri:09:14-fri:09:44',
            'PendingModifiedValues': {},
            'LatestRestorableTime': '2025-06-19T15:10:00+00:00',
            'MultiAZ': False,
            'EngineVersion': '8.0.40',
            'AutoMinorVersionUpgrade': True,
            'ReadReplicaDBInstanceIdentifiers': [],
            'LicenseModel': 'general-public-license',
            'Iops': 3000,
            'OptionGroupMemberships': [
                {'OptionGroupName': 'default:mysql-8-0', 'Status': 'in-sync'}
            ],
            'PubliclyAccessible': True,
            'StorageType': 'gp3',
            'DbInstancePort': 0,
            'StorageEncrypted': True,
            'KmsKeyId': 'arn:aws:kms:us-east-1:123456789012:key/11111111-2222-3333-4444-555555555555',
            'DbiResourceId': 'db-EXAMPLE2345678901BCDEFGH',
            'DomainMemberships': [],
            'CopyTagsToSnapshot': False,
            'MonitoringInterval': 0,
            'DBInstanceArn': 'arn:aws:rds:us-east-1:123456789012:db:example-mysql-db',
            'IAMDatabaseAuthenticationEnabled': False,
            'DatabaseInsightsMode': 'standard',
            'PerformanceInsightsEnabled': False,
            'DeletionProtection': False,
            'AssociatedRoles': [],
            'TagList': [],
            'CustomerOwnedIpEnabled': False,
            'ActivityStreamStatus': 'stopped',
            'BackupTarget': 'region',
            'NetworkType': 'IPV4',
            'StorageThroughput': 125,
            'DedicatedLogVolume': False,
            'IsStorageConfigUpgradeAvailable': False,
            'EngineLifecycleSupport': 'open-source-rds-extended-support',
        },
        {
            'DBInstanceIdentifier': 'example-db-1',
            'DBInstanceClass': 'db.m5.large',
            'Engine': 'mysql',
            'DBInstanceStatus': 'available',
            'MasterUsername': 'admin',
            'Endpoint': {
                'Address': 'example-db-1.example.us-east-1.rds.amazonaws.com',
                'Port': 3306,
                'HostedZoneId': 'EXAMPLE123456',
            },
            'AllocatedStorage': 20,
            'InstanceCreateTime': '2025-06-17T00:33:43.683000+00:00',
            'PreferredBackupWindow': '04:00-04:30',
            'BackupRetentionPeriod': 1,
            'DBSecurityGroups': [],
            'VpcSecurityGroups': [
                {'VpcSecurityGroupId': 'sg-example12345678', 'Status': 'active'}
            ],
            'DBParameterGroups': [
                {'DBParameterGroupName': 'example-db-1-params', 'ParameterApplyStatus': 'in-sync'}
            ],
            'AvailabilityZone': 'us-east-1f',
            'PreferredMaintenanceWindow': 'tue:03:20-tue:03:50',
            'PendingModifiedValues': {},
            'LatestRestorableTime': '2025-06-19T15:10:00+00:00',
            'MultiAZ': False,
            'EngineVersion': '8.0.40',
            'AutoMinorVersionUpgrade': True,
            'ReadReplicaDBInstanceIdentifiers': [],
            'LicenseModel': 'general-public-license',
            'OptionGroupMemberships': [
                {'OptionGroupName': 'default:mysql-8-0', 'Status': 'in-sync'}
            ],
            'PubliclyAccessible': True,
            'StorageType': 'gp2',
            'DbInstancePort': 0,
            'StorageEncrypted': False,
            'DbiResourceId': 'db-2REYVJKNCGOJSXNUSKHOFUHVCE',
            'DomainMemberships': [],
            'CopyTagsToSnapshot': False,
            'MonitoringInterval': 0,
            'DBInstanceArn': 'arn:aws:rds:us-east-1:941243734246:db:prod-db-1',
            'IAMDatabaseAuthenticationEnabled': False,
            'DatabaseInsightsMode': 'standard',
            'PerformanceInsightsEnabled': True,
            'PerformanceInsightsRetentionPeriod': 7,
            'DeletionProtection': False,
            'AssociatedRoles': [],
            'TagList': [],
            'CustomerOwnedIpEnabled': False,
            'ActivityStreamStatus': 'stopped',
            'BackupTarget': 'region',
            'NetworkType': 'IPV4',
            'StorageThroughput': 0,
            'DedicatedLogVolume': False,
            'IsStorageConfigUpgradeAvailable': False,
            'EngineLifecycleSupport': 'open-source-rds-extended-support',
        },
    ]
}


MOCK_DB_CLUSTERS_RESPONSE = {
    'DBClusters': [
        {
            'AllocatedStorage': 1,
            'AvailabilityZones': ['us-east-1d', 'us-east-1a', 'us-east-1b'],
            'BackupRetentionPeriod': 1,
            'DatabaseName': 'mydb',
            'DBClusterIdentifier': 'example-postgres-cluster',
            'DBClusterParameterGroup': 'default.aurora-postgresql16',
            'DBSubnetGroup': 'default',
            'Status': 'available',
            'EarliestRestorableTime': '2025-06-18T07:08:13.983000+00:00',
            'Endpoint': 'example-postgres-cluster.cluster-example.us-east-1.rds.amazonaws.com',
            'ReaderEndpoint': 'example-postgres-cluster.cluster-ro-example.us-east-1.rds.amazonaws.com',
            'MultiAZ': False,
            'Engine': 'aurora-postgresql',
            'EngineVersion': '16.6',
            'LatestRestorableTime': '2025-06-19T15:06:06.362000+00:00',
            'Port': 5432,
            'MasterUsername': 'postgres',
            'PreferredBackupWindow': '07:04-07:34',
            'PreferredMaintenanceWindow': 'sat:05:38-sat:06:08',
            'ReadReplicaIdentifiers': [],
            'DBClusterMembers': [
                {
                    'DBInstanceIdentifier': 'example-postgres-instance',
                    'IsClusterWriter': True,
                    'DBClusterParameterGroupStatus': 'in-sync',
                    'PromotionTier': 1,
                }
            ],
            'VpcSecurityGroups': [
                {'VpcSecurityGroupId': 'sg-abcdefghij1234567', 'Status': 'active'}
            ],
            'HostedZoneId': 'ABCD1234EFGH56',
            'StorageEncrypted': False,
            'DbClusterResourceId': 'cluster-ABCDEFGHIJKLMNOPQRSTUVWXYZ',
            'DBClusterArn': 'arn:aws:rds:us-east-1:123456789012:cluster:example-postgres-cluster',
            'AssociatedRoles': [],
            'IAMDatabaseAuthenticationEnabled': False,
            'ClusterCreateTime': '2025-05-28T15:45:56.941000+00:00',
            'EngineMode': 'provisioned',
            'DeletionProtection': False,
            'HttpEndpointEnabled': True,
            'ActivityStreamStatus': 'stopped',
            'CopyTagsToSnapshot': False,
            'CrossAccountClone': False,
            'DomainMemberships': [],
            'TagList': [],
            'AutoMinorVersionUpgrade': True,
            'DatabaseInsightsMode': 'standard',
            'NetworkType': 'IPV4',
            'LocalWriteForwardingStatus': 'disabled',
            'EngineLifecycleSupport': 'open-source-rds-extended-support',
        }
    ]
}
