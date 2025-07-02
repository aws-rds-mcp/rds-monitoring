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

"""aws-rds://db-cluster data models and resource implementation."""

from ...common.connection import RDSConnectionManager
from ...common.server import mcp
from ...context import Context
from loguru import logger
from mypy_boto3_rds.type_defs import DBClusterTypeDef
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


# Data Models


class ClusterOverview(BaseModel):
    """A model for the most essential information about a RDS database cluster.

    This model represents a cluster in the list of clusters returned by the `list_clusters` resource.
    It contains the fundamental identifying information and high-level status of an RDS cluster.
    """

    db_cluster_identifier: str = Field(..., description='Unique identifier for the cluster')
    db_cluster_resource_id: str = Field(
        ..., description='The unique resource identifier for this cluster'
    )
    db_cluster_arn: str = Field(..., description='ARN of the cluster')
    status: str = Field(..., description='Current status of the cluster')
    engine: str = Field(
        ..., description='Database engine type (e.g., aurora, aurora-mysql, aurora-postgresql)'
    )
    engine_version: str = Field(..., description='The version of the database engine')
    availability_zones: Optional[List[str]] = Field(
        None, description='The AZs where the cluster instances can be created'
    )
    multi_az: bool = Field(
        ..., description='Whether the cluster has instances in multiple Availability Zones'
    )
    tag_list: Optional[List[Dict[str, str]]] = Field(
        None, description='List of tags attached to the cluster'
    )


class ClusterDetails(BaseModel):
    """A model for detailed information about a RDS cluster.

    This model represents a cluster returned by the `get_cluster_details` resource.
    It provides comprehensive information about the cluster including its configuration,
    status, endpoints, member instances, and security settings.
    """

    cluster_overview: ClusterOverview = Field(..., description='Basic cluster information')

    # Storage information
    allocated_storage: Optional[int] = Field(None, description='The allocated storage size in GiB')
    storage_encrypted: Optional[bool] = Field(
        None, description='Whether the DB cluster is encrypted'
    )
    kms_key_id: Optional[str] = Field(
        None, description='The AWS KMS key identifier for the encrypted cluster'
    )
    storage_type: Optional[str] = Field(
        None, description='The storage type associated with the DB cluster'
    )
    iops: Optional[int] = Field(None, description='The Provisioned IOPS value')
    storage_throughput: Optional[int] = Field(
        None, description='The storage throughput for the DB cluster'
    )

    # Database configuration
    database_name: Optional[str] = Field(None, description='The name of the initial database')
    db_cluster_parameter_group: Optional[str] = Field(
        None, description='The name of the DB cluster parameter group'
    )
    db_subnet_group: Optional[str] = Field(
        None, description='The subnet group associated with the DB cluster'
    )

    # Network configuration
    vpc_security_groups: Optional[List[Dict[str, str]]] = Field(
        None, description='The VPC security groups that the DB cluster belongs to'
    )
    network_type: Optional[str] = Field(
        None, description='The network type of the DB cluster (IPV4/DUAL)'
    )
    publicly_accessible: Optional[bool] = Field(
        None, description='Indicates whether the DB cluster is publicly accessible'
    )

    # Status and monitoring
    cluster_create_time: Optional[str] = Field(
        None, description='When the DB cluster was created, in UTC'
    )
    earliest_restorable_time: Optional[str] = Field(
        None,
        description='The earliest time to which a database can be restored with point-in-time restore',
    )
    latest_restorable_time: Optional[str] = Field(
        None,
        description='The latest time to which a database can be restored with point-in-time restore',
    )
    status_infos: Optional[List[Dict[str, Any]]] = Field(
        None, description='Status information for the DB cluster'
    )
    percent_progress: Optional[str] = Field(
        None, description='The progress of the operation as a percentage'
    )
    performance_insights_enabled: Optional[bool] = Field(
        None, description='Whether Performance Insights is enabled for the DB cluster'
    )
    monitoring_interval: Optional[int] = Field(
        None,
        description='The interval, in seconds, between points when Enhanced Monitoring metrics are collected',
    )

    # Backup and maintenance
    backup_retention_period: Optional[int] = Field(
        None, description='The number of days for which automatic DB snapshots are retained'
    )
    preferred_backup_window: Optional[str] = Field(
        None, description='The daily time range during which automated backups are created'
    )
    preferred_maintenance_window: Optional[str] = Field(
        None, description='The weekly time range during which system maintenance can occur'
    )
    auto_minor_version_upgrade: Optional[bool] = Field(
        None, description='Whether minor version patches are applied automatically'
    )
    copy_tags_to_snapshot: Optional[bool] = Field(
        None, description='Whether tags are copied from the DB cluster to snapshots'
    )

    # Replication and scaling
    replication_source_identifier: Optional[str] = Field(
        None, description='The identifier of the source DB cluster if this is a read replica'
    )
    read_replica_identifiers: Optional[List[str]] = Field(
        None, description='The identifiers of the read replicas associated with this DB cluster'
    )
    db_cluster_members: Optional[List[Dict[str, Any]]] = Field(
        None, description='The list of instances that make up the DB cluster'
    )
    engine_mode: Optional[str] = Field(
        None, description='The DB engine mode of the DB cluster (provisioned, serverless, etc.)'
    )
    scaling_configuration_info: Optional[Dict[str, Any]] = Field(
        None, description='The scaling configuration for Aurora Serverless'
    )
    serverless_v2_scaling_configuration: Optional[Dict[str, Any]] = Field(
        None, description='The scaling configuration for Aurora Serverless v2'
    )

    # Security
    iam_database_authentication_enabled: Optional[bool] = Field(
        None, description='Whether mapping of IAM accounts to database accounts is enabled'
    )
    deletion_protection: Optional[bool] = Field(
        None, description='Whether the DB cluster has deletion protection enabled'
    )

    # Advanced features
    enabled_cloudwatch_logs_exports: Optional[List[str]] = Field(
        None, description='The log types exported to CloudWatch Logs'
    )
    backtrack_window: Optional[int] = Field(
        None, description='The target backtrack window, in seconds'
    )
    activity_stream_status: Optional[str] = Field(
        None, description='The status of the database activity stream'
    )

    # Additional details
    global_cluster_identifier: Optional[str] = Field(
        None, description='The global cluster identifier if part of a global database'
    )
    associated_roles: Optional[List[Dict[str, Any]]] = Field(
        None, description='The IAM roles associated with the DB cluster'
    )
    pending_modified_values: Optional[Dict[str, Any]] = Field(
        None, description='Information about pending changes to the DB cluster'
    )


# Helper Function


def get_cluster_overview(cluster: DBClusterTypeDef) -> ClusterOverview:
    """Extract essential details from an RDS cluster response to create an overview.

    Args:
        cluster (DBClusterTypeDef): The cluster dictionary from the AWS RDS API response

    Returns:
        ClusterOverview: A model containing key information about the RDS cluster
    """
    # Convert TagTypeDef objects to regular dictionaries if needed
    tags = cluster.get('TagList')
    converted_tags = None
    if tags:
        converted_tags = [
            {'Key': tag.get('Key', ''), 'Value': tag.get('Value', '')} for tag in tags
        ]

    return ClusterOverview(
        db_cluster_identifier=cluster.get('DBClusterIdentifier', ''),
        db_cluster_resource_id=cluster.get('DbClusterResourceId', ''),
        db_cluster_arn=cluster.get('DBClusterArn', ''),
        status=cluster.get('Status', ''),
        engine=cluster.get('Engine', ''),
        engine_version=cluster.get('EngineVersion', ''),
        availability_zones=cluster.get('AvailabilityZones'),
        multi_az=cluster.get('MultiAZ', False),
        tag_list=converted_tags,
    )


# MCP Resource Descriptions

LIST_CLUSTERS_RESOURCE_DESCRIPTION = """List all available Amazon RDS clusters in your account.

    <use_case>
    Use this resource to discover all available RDS database clusters in your AWS account,
    including Aurora clusters (MySQL/PostgreSQL) and Multi-AZ DB clusters.
    </use_case>

    <important_notes>
    1. The response provides the essential information (identifiers, engine, etc.) about each cluster
    2. Cluster identifiers returned can be used with other tools and resources in this MCP server
    3. Keep note of the db_cluster_identifier and db_cluster_resource_id for use with other tools
    4. Clusters are filtered to the AWS region specified in your environment configuration
    5. Use the `aws-rds://db-cluster/{db_cluster_identifier}` to get more information about a specific cluster
    </important_notes>

    ## Response structure
    Returns an array of DB cluster objects, each containing:
    - `db_cluster_identifier`: Unique identifier for the cluster (string)
    - `db_cluster_resource_id`: The unique resource identifier for this cluster (string)
    - `db_cluster_arn`: ARN of the cluster (string)
    - `status`: Current status of the cluster (string)
    - `engine`: Database engine type (string)
    - `engine_version`: The version of the database engine (string)
    - `availability_zones`: The AZs where the cluster instances can be created (array of strings)
    - `multi_az`: Whether the cluster has instances in multiple Availability Zones (boolean)
    - `tag_list`: List of tags attached to the cluster

    <examples>
    Example usage scenarios:
    1. Discovery and inventory:
       - List all available RDS clusters to create an inventory
       - Identify cluster engine types and versions in your environment

    2. Preparation for other operations:
       - Find specific cluster identifiers to use with management tools
       - Identify clusters that may need maintenance or upgrades
    </examples>
    """

GET_CLUSTER_DETAIL_RESOURCE_DESCRIPTION = """Get detailed information about a specific RDS cluster.

    <use_case>
    Use this resource to retrieve comprehensive details about a specific RDS cluster,
    including its instances, networking, and configuration.
    </use_case>

    <important_notes>
    1. The response provides the essential information (identifiers, engine, etc.) about each cluster
    2. Cluster identifiers returned can be used with other tools and resources in this MCP server
    3. Keep note of the db_cluster_identifier and db_cluster_resource_id for use with other tools
    4. Clusters are filtered to the AWS region specified in your environment configuration
    5. Use the `aws-rds://db-cluster/{db_cluster_identifier}` to get more information about a specific cluster
    </important_notes>

    ## Response structure
    Returns an array of DB cluster objects, each containing:
    - `db_cluster_identifier`: Unique identifier for the cluster (string)
    - `db_cluster_resource_id`: The unique resource identifier for this cluster (string)
    - `db_cluster_arn`: ARN of the cluster (string)
    - `status`: Current status of the cluster (string)
    - `engine`: Database engine type (string)
    - `engine_version`: The version of the database engine (string)
    - `availability_zones`: The AZs where the cluster instances can be created (array of strings)
    - `multi_az`: Whether the cluster has instances in multiple Availability Zones (boolean)
    - `tag_list`: List of tags attached to the cluster

    <examples>
    Example usage scenarios:
    1. Discovery and inventory:
       - List all available RDS clusters to create an inventory
       - Identify cluster engine types and versions in your environment

    2. Preparation for other operations:
       - Find specific cluster identifiers to use with management tools
       - Identify clusters that may need maintenance or upgrades
    </examples>
    """

# MCP Resources


@mcp.resource(
    uri='aws-rds://db-cluster',
    name='ListClusters',
    mime_type='application/json',
    description=LIST_CLUSTERS_RESOURCE_DESCRIPTION,
)
async def list_clusters() -> List[ClusterOverview]:
    """Retrieve a list of all RDS clusters available in the account.

    Returns:
        List[ClusterOverview]: A list of models containing key information about each RDS cluster
    """
    clusters: List[ClusterOverview] = []
    rds_client = RDSConnectionManager.get_connection()
    paginator = rds_client.get_paginator('describe_db_clusters')
    page_iterator = paginator.paginate(PaginationConfig=Context.get_pagination_config())

    for page in page_iterator:
        for cluster in page.get('DBClusters', []):
            cluster_item = get_cluster_overview(cluster)
            clusters.append(cluster_item)
            logger.debug(f'Retrieved cluster information for {cluster_item.db_cluster_identifier}')

    return clusters


@mcp.resource(
    uri='aws-rds://db-cluster/{db_cluster_identifier}',
    name='GetClusterDetails',
    mime_type='application/json',
    description=GET_CLUSTER_DETAIL_RESOURCE_DESCRIPTION,
)
async def get_cluster_details(db_cluster_identifier: str) -> ClusterDetails:
    """Get detailed information about a specific RDS cluster.

    Args:
        db_cluster_identifier (str): The identifier of the RDS cluster to retrieve

    Returns:
        ClusterDetails: A model containing detailed information about the RDS cluster

    Raises:
        Exception: If the specified cluster is not found or another error occurs
    """
    rds_client = RDSConnectionManager.get_connection()
    response = rds_client.describe_db_clusters(DBClusterIdentifier=db_cluster_identifier)

    cluster = response['DBClusters'][0]
    logger.debug(f'Retrieved cluster details for {db_cluster_identifier}')

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
