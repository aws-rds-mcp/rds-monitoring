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
from typing import Dict, List, Optional


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
