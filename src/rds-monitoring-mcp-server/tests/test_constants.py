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
            'DBInstanceIdentifier': 'test-db-instance-1',
            'DBInstanceClass': 'db.t3.medium',
            'Engine': 'mysql',
            'DBInstanceStatus': 'available',
            'MasterUsername': 'admin',
            'Endpoint': {
                'Address': 'test-db-instance-1.abc123.us-east-1.rds.amazonaws.com',
                'Port': 3306,
                'HostedZoneId': 'Z1PVIF0B656C1W',
            },
            'AllocatedStorage': 20,
            'InstanceCreateTime': '2025-01-15T00:00:00+00:00',
            'PreferredBackupWindow': '07:00-08:00',
            'BackupRetentionPeriod': 7,
            'DBSecurityGroups': [],
            'VpcSecurityGroups': [{'VpcSecurityGroupId': 'sg-12345', 'Status': 'active'}],
            'DBParameterGroups': [
                {'DBParameterGroupName': 'default.mysql8.0', 'ParameterApplyStatus': 'in-sync'}
            ],
            'AvailabilityZone': 'us-east-1a',
            'DBSubnetGroup': {
                'DBSubnetGroupName': 'default',
                'DBSubnetGroupDescription': 'default',
                'VpcId': 'vpc-12345',
                'SubnetGroupStatus': 'Complete',
                'Subnets': [
                    {
                        'SubnetIdentifier': 'subnet-12345',
                        'SubnetAvailabilityZone': {'Name': 'us-east-1a'},
                        'SubnetStatus': 'Active',
                    },
                    {
                        'SubnetIdentifier': 'subnet-67890',
                        'SubnetAvailabilityZone': {'Name': 'us-east-1b'},
                        'SubnetStatus': 'Active',
                    },
                ],
            },
            'MultiAZ': False,
            'EngineVersion': '8.0.28',
            'AutoMinorVersionUpgrade': True,
            'ReadReplicaDBInstanceIdentifiers': [],
            'LicenseModel': 'general-public-license',
            'OptionGroupMemberships': [
                {'OptionGroupName': 'default:mysql-8-0', 'Status': 'in-sync'}
            ],
            'PubliclyAccessible': False,
            'StorageType': 'gp2',
            'DbInstancePort': 0,
            'StorageEncrypted': True,
            'KmsKeyId': 'arn:aws:kms:us-east-1:123456789012:key/abcd1234-ab12-cd34-ef56-123456789012',
            'DbiResourceId': 'db-ABCDEFGHIJKLMNOPQRSTUVWXYZ',
            'CACertificateIdentifier': 'rds-ca-2019',
            'DomainMemberships': [],
            'CopyTagsToSnapshot': True,
            'MonitoringInterval': 60,
            'EnhancedMonitoringResourceArn': 'arn:aws:logs:us-east-1:123456789012:log-group:RDSOSMetrics:log-stream:db-ABCDEFGHIJKLMNOPQRSTUVWXYZ',
            'MonitoringRoleArn': 'arn:aws:iam::123456789012:role/rds-monitoring-role',
            'PerformanceInsightsEnabled': True,
            'PerformanceInsightsKMSKeyId': 'arn:aws:kms:us-east-1:123456789012:key/abcd1234-ab12-cd34-ef56-123456789012',
            'PerformanceInsightsRetentionPeriod': 7,
            'DeletionProtection': True,
            'MaxAllocatedStorage': 1000,
            'TagList': [
                {'Key': 'Environment', 'Value': 'Test'},
                {'Key': 'Project', 'Value': 'RDS Monitoring'},
            ],
        },
        {
            'DBInstanceIdentifier': 'test-db-instance-2',
            'DBInstanceClass': 'db.m5.large',
            'Engine': 'postgres',
            'DBInstanceStatus': 'available',
            'MasterUsername': 'postgres',
            'Endpoint': {
                'Address': 'test-db-instance-2.abc456.us-east-1.rds.amazonaws.com',
                'Port': 5432,
                'HostedZoneId': 'Z1PVIF0B656C1W',
            },
            'AllocatedStorage': 50,
            'InstanceCreateTime': '2025-02-20T00:00:00+00:00',
            'PreferredBackupWindow': '08:00-09:00',
            'BackupRetentionPeriod': 14,
            'DBSecurityGroups': [],
            'VpcSecurityGroups': [{'VpcSecurityGroupId': 'sg-67890', 'Status': 'active'}],
            'DBParameterGroups': [
                {'DBParameterGroupName': 'default.postgres14', 'ParameterApplyStatus': 'in-sync'}
            ],
            'AvailabilityZone': 'us-east-1c',
            'DBSubnetGroup': {
                'DBSubnetGroupName': 'default',
                'DBSubnetGroupDescription': 'default',
                'VpcId': 'vpc-67890',
                'SubnetGroupStatus': 'Complete',
                'Subnets': [
                    {
                        'SubnetIdentifier': 'subnet-abcde',
                        'SubnetAvailabilityZone': {'Name': 'us-east-1c'},
                        'SubnetStatus': 'Active',
                    },
                    {
                        'SubnetIdentifier': 'subnet-fghij',
                        'SubnetAvailabilityZone': {'Name': 'us-east-1d'},
                        'SubnetStatus': 'Active',
                    },
                ],
            },
            'MultiAZ': True,
            'EngineVersion': '14.3',
            'AutoMinorVersionUpgrade': True,
            'ReadReplicaDBInstanceIdentifiers': [],
            'LicenseModel': 'postgresql-license',
            'OptionGroupMemberships': [
                {'OptionGroupName': 'default:postgres-14', 'Status': 'in-sync'}
            ],
            'PubliclyAccessible': False,
            'StorageType': 'io1',
            'Iops': 3000,
            'DbInstancePort': 0,
            'StorageEncrypted': True,
            'KmsKeyId': 'arn:aws:kms:us-east-1:123456789012:key/efgh5678-ef56-gh78-ij90-456789012345',
            'DbiResourceId': 'db-ZYXWVUTSRQPONMLKJIHGFEDCBA',
            'CACertificateIdentifier': 'rds-ca-2019',
            'DomainMemberships': [],
            'CopyTagsToSnapshot': True,
            'MonitoringInterval': 30,
            'EnhancedMonitoringResourceArn': 'arn:aws:logs:us-east-1:123456789012:log-group:RDSOSMetrics:log-stream:db-ZYXWVUTSRQPONMLKJIHGFEDCBA',
            'MonitoringRoleArn': 'arn:aws:iam::123456789012:role/rds-monitoring-role',
            'PerformanceInsightsEnabled': True,
            'PerformanceInsightsKMSKeyId': 'arn:aws:kms:us-east-1:123456789012:key/efgh5678-ef56-gh78-ij90-456789012345',
            'PerformanceInsightsRetentionPeriod': 7,
            'DeletionProtection': True,
            'MaxAllocatedStorage': 1000,
            'TagList': [
                {'Key': 'Environment', 'Value': 'Production'},
                {'Key': 'Project', 'Value': 'RDS Monitoring'},
            ],
        },
    ]
}

MOCK_DB_CLUSTERS_RESPONSE = {
    'DBClusters': [
        {
            'DBClusterIdentifier': 'test-aurora-cluster',
            'Engine': 'aurora-mysql',
            'EngineVersion': '5.7.mysql_aurora.2.10.2',
            'Status': 'available',
            'DBClusterMembers': [
                {
                    'DBInstanceIdentifier': 'test-aurora-instance-1',
                    'IsClusterWriter': True,
                    'DBClusterParameterGroupStatus': 'in-sync',
                    'PromotionTier': 1,
                },
                {
                    'DBInstanceIdentifier': 'test-aurora-instance-2',
                    'IsClusterWriter': False,
                    'DBClusterParameterGroupStatus': 'in-sync',
                    'PromotionTier': 2,
                },
            ],
            'VpcSecurityGroups': [{'VpcSecurityGroupId': 'sg-abcde', 'Status': 'active'}],
            'HostedZoneId': 'Z1PVIF0B656C1W',
            'StorageEncrypted': True,
            'KmsKeyId': 'arn:aws:kms:us-east-1:123456789012:key/abcd1234-ab12-cd34-ef56-123456789012',
            'DbClusterResourceId': 'cluster-ABCDEFGHIJKLMNOPQRSTUVWXYZ',
            'Endpoint': 'test-aurora-cluster.cluster-abc123.us-east-1.rds.amazonaws.com',
            'ReaderEndpoint': 'test-aurora-cluster.cluster-ro-abc123.us-east-1.rds.amazonaws.com',
            'MultiAZ': True,
            'EngineMode': 'provisioned',
            'DBClusterParameterGroup': 'default.aurora-mysql5.7',
            'DBSubnetGroup': 'default',
            'AvailabilityZones': ['us-east-1a', 'us-east-1b', 'us-east-1c'],
            'BackupRetentionPeriod': 7,
            'PreferredBackupWindow': '07:00-08:00',
            'PreferredMaintenanceWindow': 'sat:12:00-sat:13:30',
            'TagList': [
                {'Key': 'Environment', 'Value': 'Production'},
                {'Key': 'Project', 'Value': 'Aurora Cluster'},
            ],
        }
    ]
}
