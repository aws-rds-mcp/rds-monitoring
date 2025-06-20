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

from awslabs.rds_monitoring_mcp_server.models import (
    ClusterOverview,
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
    page_iterator = paginator.paginate()

    for page in page_iterator:
        for instance in page.get('DBInstances', []):
            instance_item: InstanceOverview = {}
            instance_item = get_instance_overview(instance)
            instances.append(instance_item)
            logger.debug(
                f'Retrieved instance information for {instance_item.db_instance_identifier}'
            )

    return instances


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
    page_iterator = paginator.paginate()

    for page in page_iterator:
        for cluster in page.get('DBClusters', []):
            cluster_item = get_cluster_overview(cluster)
            clusters.append(cluster_item)
            logger.debug(f'Retrieved cluster information for {cluster_item.db_cluster_identifier}')

    return clusters
