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

"""Data models for the RDS Monitoring MCP Server."""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


# Instance & Cluster Models


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
