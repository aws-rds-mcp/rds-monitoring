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

from .utils import handle_aws_error
from awslabs.rds_monitoring_mcp_server.constants import PAGINATION_CONFIG
from awslabs.rds_monitoring_mcp_server.models import (
    ClusterDetails,
    ClusterOverview,
    InstanceDetails,
    InstanceOverview,
)
from loguru import logger
from mypy_boto3_rds import RDSClient
from typing import List


# General Utility Functions


def get_instance_overview(instance: dict) -> InstanceOverview:
    """Extract essential details from an RDS instance response to create an overview.

    Args:
        instance (dict): The instance dictionary from the AWS RDS API response

    Returns:
        InstanceOverview: A model containing key information about the RDS instance
    """
    return InstanceOverview(
        db_instance_identifier=instance.get('DBInstanceIdentifier'),
        dbi_resource_id=instance.get('DbiResourceId'),
        db_instance_arn=instance.get('DBInstanceArn'),
        db_instance_status=instance.get('DBInstanceStatus'),
        db_instance_class=instance.get('DBInstanceClass'),
        engine=instance.get('Engine'),
        availability_zone=instance.get('AvailabilityZone'),
        multi_az=instance.get('MultiAZ', False),
        tag_list=instance.get('TagList'),
    )


def get_cluster_overview(cluster: dict) -> ClusterOverview:
    """Extract essential details from an RDS cluster response to create an overview.

    Args:
        cluster (dict): The cluster dictionary from the AWS RDS API response

    Returns:
        ClusterOverview: A model containing key information about the RDS cluster
    """
    return ClusterOverview(
        db_cluster_identifier=cluster.get('DBClusterIdentifier'),
        db_cluster_resource_id=cluster.get('DbClusterResourceId'),
        db_cluster_arn=cluster.get('DBClusterArn'),
        status=cluster.get('Status'),
        engine=cluster.get('Engine'),
        engine_version=cluster.get('EngineVersion'),
        availability_zones=cluster.get('AvailabilityZones'),
        multi_az=cluster.get('MultiAZ', False),
        tag_list=cluster.get('TagList'),
    )


# Instance Discovery


async def list_instances(rds_client: RDSClient) -> List[InstanceOverview]:
    """Retrieve a list of all RDS instances available in the account.

    Args:
        rds_client (RDSClient): The boto3 RDS client for making API calls

    Returns:
        List[InstanceOverview]: A list of models containing key information about each RDS instance
    """
    instances: List[InstanceOverview] = []
    paginator = rds_client.get_paginator('describe_db_instances')
    page_iterator = paginator.paginate(PaginationConfig=PAGINATION_CONFIG)

    for page in page_iterator:
        for instance in page.get('DBInstances', []):
            instance_item: InstanceOverview = {}
            instance_item = get_instance_overview(instance)
            instances.append(instance_item)
            logger.debug(
                f'Retrieved instance information for {instance_item.db_instance_identifier}'
            )

    return instances


async def get_instance_details(
    rds_client: RDSClient, db_instance_identifier: str
) -> InstanceDetails:
    """Get detailed information about a specific RDS instance.

    Args:
        rds_client (RDSClient): The boto3 RDS client for making API calls
        db_instance_identifier (str): The identifier of the RDS instance to retrieve

    Returns:
        InstanceDetails: A model containing detailed information about the RDS instance

    Raises:
        Exception: If the specified instance is not found or another error occurs
    """
    try:
        response = rds_client.describe_db_instances(DBInstanceIdentifier=db_instance_identifier)
    except Exception as e:
        return await handle_aws_error('describe_db_instances({db_instance_identifier})', e, None)

    instance = response['DBInstances'][0]
    logger.debug(f'Retrieved instance details for {db_instance_identifier}')

    # Extract VPC security groups
    vpc_security_groups = [
        {'vpc_security_group_id': sg.get('VpcSecurityGroupId'), 'status': sg.get('Status')}
        for sg in instance.get('VpcSecurityGroups', [])
    ]

    # Extract DB parameter groups
    db_parameter_groups = [
        {'name': pg.get('DBParameterGroupName'), 'status': pg.get('ParameterApplyStatus')}
        for pg in instance.get('DBParameterGroups', [])
    ]

    # Create the InstanceDetails object
    instance_details = InstanceDetails(
        instance_overview=get_instance_overview(instance),
        # Storage information
        allocated_storage=instance.get('AllocatedStorage'),
        storage_type=instance.get('StorageType'),
        storage_encrypted=instance.get('StorageEncrypted'),
        storage_throughput=instance.get('StorageThroughput'),
        iops=instance.get('Iops'),
        max_allocated_storage=instance.get('MaxAllocatedStorage'),
        # Database configuration
        db_name=instance.get('DBName'),
        engine_version=instance.get('EngineVersion'),
        # Network configuration
        vpc_id=instance.get('DBSubnetGroup', {}).get('VpcId'),
        publicly_accessible=instance.get('PubliclyAccessible'),
        vpc_security_groups=vpc_security_groups,
        network_type=instance.get('NetworkType'),
        db_subnet_group_name=instance.get('DBSubnetGroup', {}).get('DBSubnetGroupName'),
        # Status and monitoring
        instance_create_time=str(instance.get('InstanceCreateTime'))
        if instance.get('InstanceCreateTime')
        else None,
        latest_restorable_time=str(instance.get('LatestRestorableTime'))
        if instance.get('LatestRestorableTime')
        else None,
        performance_insights_enabled=instance.get('PerformanceInsightsEnabled'),
        # Backup and maintenance
        backup_retention_period=instance.get('BackupRetentionPeriod'),
        preferred_backup_window=instance.get('PreferredBackupWindow'),
        preferred_maintenance_window=instance.get('PreferredMaintenanceWindow'),
        auto_minor_version_upgrade=instance.get('AutoMinorVersionUpgrade'),
        copy_tags_to_snapshot=instance.get('CopyTagsToSnapshot'),
        # Configuration groups
        db_parameter_groups=db_parameter_groups,
        # Read replicas
        read_replica_source_db_instance_identifier=instance.get(
            'ReadReplicaSourceDBInstanceIdentifier'
        ),
        read_replica_db_instance_identifiers=instance.get('ReadReplicaDBInstanceIdentifiers'),
        # Additional details
        pending_modified_values=instance.get('PendingModifiedValues'),
        status_infos=instance.get('StatusInfos'),
        processor_features=instance.get('ProcessorFeatures'),
        character_set_name=instance.get('CharacterSetName'),
        timezone=instance.get('Timezone'),
    )

    return instance_details


# Cluster Discovery


async def list_clusters(
    rds_client: RDSClient,
) -> List[ClusterOverview]:
    """Retrieve a list of all RDS clusters available in the account.

    Args:
        rds_client (RDSClient): The boto3 RDS client for making API calls

    Returns:
        List[ClusterOverview]: A list of models containing key information about each RDS cluster
    """
    clusters: List[ClusterOverview] = []
    paginator = rds_client.get_paginator('describe_db_clusters')
    page_iterator = paginator.paginate(PaginationConfig=PAGINATION_CONFIG)

    for page in page_iterator:
        for cluster in page.get('DBClusters', []):
            cluster_item = get_cluster_overview(cluster)
            clusters.append(cluster_item)
            logger.debug(f'Retrieved cluster information for {cluster_item.db_cluster_identifier}')

    return clusters


async def get_cluster_details(rds_client: RDSClient, cluster_identifier: str) -> ClusterDetails:
    """Get detailed information about a specific RDS cluster.

    Args:
        rds_client (RDSClient): The boto3 RDS client for making API calls
        cluster_identifier (str): The identifier of the RDS cluster to retrieve

    Returns:
        ClusterDetails: A model containing detailed information about the RDS cluster

    Raises:
        Exception: If the specified cluster is not found or another error occurs
    """
    try:
        response = rds_client.describe_db_clusters(DBClusterIdentifier=cluster_identifier)
    except Exception as e:
        return await handle_aws_error('describe_db_instances({db_instance_identifier})', e, None)

    cluster = response['DBClusters'][0]
    logger.debug(f'Retrieved cluster details for {cluster_identifier}')

    # Extract VPC security groups
    vpc_security_groups = [
        {'vpc_security_group_id': sg.get('VpcSecurityGroupId'), 'status': sg.get('Status')}
        for sg in cluster.get('VpcSecurityGroups', [])
    ]

    # Extract DB cluster members
    db_cluster_members = [
        {
            'db_instance_identifier': member.get('DBInstanceIdentifier'),
            'is_cluster_writer': member.get('IsClusterWriter'),
            'db_cluster_parameter_group_status': member.get('DBClusterParameterGroupStatus'),
            'promotion_tier': member.get('PromotionTier'),
        }
        for member in cluster.get('DBClusterMembers', [])
    ]

    # Create the ClusterDetails object
    cluster_details = ClusterDetails(
        cluster_overview=get_cluster_overview(cluster),
        # Storage information
        allocated_storage=cluster.get('AllocatedStorage'),
        storage_encrypted=cluster.get('StorageEncrypted'),
        kms_key_id=cluster.get('KmsKeyId'),
        storage_type=cluster.get('StorageType'),
        iops=cluster.get('Iops'),
        storage_throughput=cluster.get('StorageThroughput'),
        # Database configuration
        database_name=cluster.get('DatabaseName'),
        db_cluster_parameter_group=cluster.get('DBClusterParameterGroup'),
        db_subnet_group=cluster.get('DBSubnetGroup'),
        # Network configuration
        vpc_security_groups=vpc_security_groups,
        network_type=cluster.get('NetworkType'),
        publicly_accessible=cluster.get('PubliclyAccessible'),
        # Status and monitoring
        cluster_create_time=str(cluster.get('ClusterCreateTime'))
        if cluster.get('ClusterCreateTime')
        else None,
        earliest_restorable_time=str(cluster.get('EarliestRestorableTime'))
        if cluster.get('EarliestRestorableTime')
        else None,
        latest_restorable_time=str(cluster.get('LatestRestorableTime'))
        if cluster.get('LatestRestorableTime')
        else None,
        status_infos=cluster.get('StatusInfos'),
        percent_progress=cluster.get('PercentProgress'),
        performance_insights_enabled=cluster.get('PerformanceInsightsEnabled'),
        monitoring_interval=cluster.get('MonitoringInterval'),
        # Backup and maintenance
        backup_retention_period=cluster.get('BackupRetentionPeriod'),
        preferred_backup_window=cluster.get('PreferredBackupWindow'),
        preferred_maintenance_window=cluster.get('PreferredMaintenanceWindow'),
        auto_minor_version_upgrade=cluster.get('AutoMinorVersionUpgrade'),
        copy_tags_to_snapshot=cluster.get('CopyTagsToSnapshot'),
        # Replication and scaling
        replication_source_identifier=cluster.get('ReplicationSourceIdentifier'),
        read_replica_identifiers=cluster.get('ReadReplicaIdentifiers'),
        db_cluster_members=db_cluster_members,
        engine_mode=cluster.get('EngineMode'),
        scaling_configuration_info=cluster.get('ScalingConfigurationInfo'),
        serverless_v2_scaling_configuration=cluster.get('ServerlessV2ScalingConfiguration'),
        # Security
        iam_database_authentication_enabled=cluster.get('IAMDatabaseAuthenticationEnabled'),
        deletion_protection=cluster.get('DeletionProtection'),
        # Advanced features
        enabled_cloudwatch_logs_exports=cluster.get('EnabledCloudwatchLogsExports'),
        backtrack_window=cluster.get('BacktrackWindow'),
        activity_stream_status=cluster.get('ActivityStreamStatus'),
        # Additional details
        global_cluster_identifier=cluster.get('GlobalClusterIdentifier'),
        associated_roles=cluster.get('AssociatedRoles'),
        pending_modified_values=cluster.get('PendingModifiedValues'),
    )

    return cluster_details
