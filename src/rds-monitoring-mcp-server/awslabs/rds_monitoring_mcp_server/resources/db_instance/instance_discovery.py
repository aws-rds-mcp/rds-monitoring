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

"""aws-rds://db-instance data models and resource implementation."""

from ...common.connection import RDSConnectionManager
from ...common.decorators import conditional_mcp_register
from ...context import Context
from loguru import logger
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class InstanceOverview(BaseModel):
    """A model for the most essential information about a RDS database instance.

    This model represents an instance in the list of instances returned by the `list_instances` resource.
    """

    db_instance_identifier: str = Field(..., description='Unique identifier for the instance')
    dbi_resource_id: str = Field(
        ..., description='The unique resource identifier for this instance'
    )
    db_instance_arn: str = Field(..., description='ARN of the instance')
    db_instance_status: str = Field(..., description='Current status of the instance')
    db_instance_class: str = Field(..., description='The compute and memory capacity class')
    engine: str = Field(..., description='Database engine type')
    availability_zone: Optional[str] = Field(None, description='The AZ where the instance resides')
    multi_az: bool = Field(..., description='Whether the instance is Multi-AZ')
    tag_list: Optional[List[Dict[str, str]]] = Field(
        None, description='List of tags attached to the instance'
    )


class InstanceDetails(BaseModel):
    """A model for a detailed information about a RDS instance.

    This model represents an instance returned by the `get_instance_details` resource.
    """

    instance_overview: InstanceOverview = Field(..., description='Basic instance information')

    # Storage Information
    allocated_storage: Optional[int] = Field(None, description='The allocated storage size in GiB')
    storage_type: Optional[str] = Field(
        None, description='The storage type for the instance (e.g. gp2, io1, standard)'
    )
    storage_encrypted: Optional[bool] = Field(
        None, description='Whether the DB instance storage is encrypted'
    )
    storage_throughput: Optional[int] = Field(
        None, description='The storage throughput for the DB instance (gp3 only)'
    )
    iops: Optional[int] = Field(None, description='The Provisioned IOPS value')
    max_allocated_storage: Optional[int] = Field(
        None, description='The upper limit for storage autoscaling'
    )

    # Database configuration
    db_name: Optional[str] = Field(None, description='The name of the database on this instance')
    engine_version: Optional[str] = Field(None, description='The version of the database engine')

    # Network configuration
    vpc_id: Optional[str] = Field(None, description='The VPC ID the DB instance is in')
    publicly_accessible: Optional[bool] = Field(
        None, description='Whether the DB instance is publicly accessible'
    )
    vpc_security_groups: Optional[List[Dict[str, str]]] = Field(
        None, description='The VPC security groups this instance belongs to'
    )
    network_type: Optional[str] = Field(None, description='The network type (IPV4, DUAL)')
    db_subnet_group_name: Optional[str] = Field(None, description='The name of the subnet group')

    # Status and monitoring
    instance_create_time: Optional[str] = Field(
        None, description='The date and time when the DB instance was created'
    )
    latest_restorable_time: Optional[str] = Field(
        None,
        description='Latest time to which a database can be restored with point-in-time restore',
    )
    performance_insights_enabled: Optional[bool] = Field(
        None, description='Whether Performance Insights is enabled'
    )

    # Backup and maintenance
    backup_retention_period: Optional[int] = Field(
        None, description='The number of days for which automated backups are retained'
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
        None, description='Whether tags are copied from the DB instance to snapshots'
    )

    # Configuration groups
    db_parameter_groups: Optional[List[Dict[str, str]]] = Field(
        None, description='The parameter groups applied to this instance'
    )

    # Read replicas
    read_replica_source_db_instance_identifier: Optional[str] = Field(
        None, description='The identifier of the source DB instance if this is a read replica'
    )
    read_replica_db_instance_identifiers: Optional[List[str]] = Field(
        None, description='The identifiers of read replicas associated with this instance'
    )

    # Additional details
    pending_modified_values: Optional[Dict[str, Any]] = Field(
        None, description='Pending changes to the DB instance'
    )
    status_infos: Optional[List[Dict[str, Any]]] = Field(
        None, description='Status information for a read replica'
    )
    processor_features: Optional[List[Dict[str, str]]] = Field(
        None, description='CPU cores and threads per core for the instance class'
    )
    character_set_name: Optional[str] = Field(
        None, description='Character set for this instance if applicable'
    )
    timezone: Optional[str] = Field(
        None, description='The time zone of the DB instance if applicable'
    )


# Helper Functions


def get_instance_overview(instance: dict) -> InstanceOverview:
    """Extract essential details from an RDS instance response to create an overview.

    Args:
        instance (dict): The instance dictionary from the AWS RDS API response

    Returns:
        InstanceOverview: A model containing key information about the RDS instance
    """
    return InstanceOverview(
        db_instance_identifier=instance.get('DBInstanceIdentifier', ''),
        dbi_resource_id=instance.get('DbiResourceId', ''),
        db_instance_arn=instance.get('DBInstanceArn', ''),
        db_instance_status=instance.get('DBInstanceStatus', ''),
        db_instance_class=instance.get('DBInstanceClass', ''),
        engine=instance.get('Engine', ''),
        availability_zone=instance.get('AvailabilityZone'),
        multi_az=instance.get('MultiAZ', False),
        tag_list=instance.get('TagList'),
    )


# MCP Resource Arguments

LIST_INSTANCES_RESOURCE_DESCRIPTION = """List all available Amazon RDS instances in your account.

    <use_case>
    Use this resource to discover all available RDS database instances in your AWS account. The list includes both standalone instances and instances that
    are part of Aurora clusters.
    </use_case>

    <important_notes>
    1. The response provides the essential information (identifiers, engine, etc.) about each instance
    2. Instance identifiers returned can be used with other tools and resources in this MCP server
    3. Keep note of the DBInstanceIdentifier and DbiResourceId for use with other tools
    4. Instances are filtered to the AWS region specified in your environment configuration
    5. Use the `aws-rds://db-instance/{db_instance_identifier}` resource to get more information (networking, cluster membership details etc.) about a specific instance
    </important_notes>

    ## Response structure
    Returns an array of DB instance objects, each containing:
    - `DBInstanceIdentifier`: Unique identifier for the instance (string)
    - `DbiResourceId`: The unqiue resource identifier for this instance (string)
    - `DBInstanceArn`: ARN of the instance (string)
    - `DBInstanceStatus`: Current status of the instance (string)
    - `DBInstanceClass`: The compute and memory capacity class (string)
    - `Engine`: Database engine type (string)
    - `AvailabilityZone`: The AZ where the instance resides (string)
    - `MultiAZ`: Whether the instance is Multi-AZ (boolean)
    - `TagList`: List of tags attached to the instance

    <examples>
    Example usage scenarios:
    1. Discovery and inventory:
       - List all available RDS instances to create an inventory

    2. Preparation for other operations:
       - Find specific instance identifiers to use with performance monitoring tools
       - Identify instances to check for events or read logs from
    </examples>
    """

GET_INSTANCE_DETAIL_RESOURCE_DESCRIPTION = """Get detailed information about a specific RDS instance.

    <use_case>
    Use this resource to retrieve comprehensive details about a specific RDS instance,
    including its networking, configuration, and performance metrics.
    </use_case>

    <important_notes>
    1. The response provides the essential information (identifiers, engine, etc.) about each instance
    2. Instance identifiers returned can be used with other tools and resources in this MCP server
    3. Keep note of the DBInstanceIdentifier and DbiResourceId for use with other tools
    4. Instances are filtered to the AWS region specified in your environment configuration
    5. Use the `aws-rds://db-instance/{db_instance_identifier}` to get more information about a specific instance
    </important_notes>

    ## Response structure
    Returns an array of DB instance objects, each containing:
    - `DBInstanceIdentifier`: Unique identifier for the instance (string)
    - `DbiResourceId`: The unique resource identifier for this instance (string)
    - `DBInstanceArn`: ARN of the instance (string)
    - `DBInstanceStatus`: Current status of the instance (string)
    - `DBInstanceClass`: The compute and memory capacity class (string)
    - `Engine`: Database engine type (string)
    - `AvailabilityZone`: The AZ where the instance resides (string)
    - `MultiAZ`: Whether the instance is Multi-AZ (boolean)
    - `TagList`: List of tags attached to the instance

    <examples>
    Example usage scenarios:
    1. Discovery and inventory:
       - List all available RDS instances to create an inventory

    2. Preparation for other operations:
       - Find specific instance identifiers to use with performance monitoring tools
       - Identify instances that may need maintenance or upgrades
    </examples>
    """


list_instances_resource_params = {
    'uri': 'aws-rds://db-instance',
    'name': 'ListRDSInstances',
    'mime_type': 'application/json',
    'description': LIST_INSTANCES_RESOURCE_DESCRIPTION,
}

list_instances_tool_params = {
    'name': 'ListRDSInstances',
    'description': LIST_INSTANCES_RESOURCE_DESCRIPTION,
}


@conditional_mcp_register(list_instances_resource_params, list_instances_tool_params)
async def list_instances() -> List[InstanceOverview]:
    """Retrieve a list of all RDS instances available in the account.

    Returns:
        List[InstanceOverview]: A list of models containing key information about each RDS instance
    """
    instances: List[InstanceOverview] = []
    rds_client = RDSConnectionManager.get_connection()
    paginator = rds_client.get_paginator('describe_db_instances')
    page_iterator = paginator.paginate(PaginationConfig=Context.get_pagination_config())

    for page in page_iterator:
        for instance in page.get('DBInstances', []):
            instance_item = get_instance_overview(instance)
            instances.append(instance_item)
            logger.debug(
                f'Retrieved instance information for {instance_item.db_instance_identifier}'
            )

    return instances


get_instance_details_resource_params = {
    'uri': 'aws-rds://db-instance/{db_instance_identifier}',
    'name': 'GetRDSInstanceDetails',
    'mime_type': 'application/json',
    'description': GET_INSTANCE_DETAIL_RESOURCE_DESCRIPTION,
}

get_instance_details_tool_params = {
    'name': 'GetRDSInstanceDetails',
    'description': GET_INSTANCE_DETAIL_RESOURCE_DESCRIPTION,
}


@conditional_mcp_register(get_instance_details_resource_params, get_instance_details_tool_params)
async def get_instance_details(db_instance_identifier: str) -> InstanceDetails:
    """Get detailed information about a specific RDS instance.

    Args:
        db_instance_identifier (str): The identifier of the RDS instance to retrieve

    Returns:
        InstanceDetails: A model containing detailed information about the RDS instance

    Raises:
        Exception: If the specified instance is not found or another error occurs
    """
    rds_client = RDSConnectionManager.get_connection()
    response = rds_client.describe_db_instances(DBInstanceIdentifier=db_instance_identifier)

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
