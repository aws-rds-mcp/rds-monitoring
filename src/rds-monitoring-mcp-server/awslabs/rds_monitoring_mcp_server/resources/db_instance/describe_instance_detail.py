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

"""Resource for retrieving detailed information about RDS DB Instances."""

import asyncio
from ...common.connection import RDSConnectionManager
from ...common.decorators.handle_exceptions import handle_exceptions
from ...common.decorators.register_mcp_primitive import register_mcp_primitive_by_context
from loguru import logger
from mypy_boto3_rds.type_defs import DBInstanceTypeDef
from pydantic import BaseModel, Field
from typing import Optional


DESCRIBE_INSTANCE_DETAIL_DOCSTRING = """Get detailed information about a specific Amazon RDS instance.

This resource retrieves comprehensive details about a specific RDS database instance identified by its instance ID, including configuration, status, endpoints, storage details, and security settings.
"""


class Instance(BaseModel):
    """DB instance response model."""

    instance: DBInstanceTypeDef = Field(..., description='The raw instance data from AWS')
    resource_uri: Optional[str] = Field(None, description='The resource URI for this instance')

    @classmethod
    def from_DBInstanceTypeDef(cls, instance: DBInstanceTypeDef) -> 'Instance':
        """Takes raw instance data from AWS and formats it into a structured Instance model.

        Args:
            instance: Raw instance data from AWS

        Returns:
            Instance: Formatted instance information with comprehensive details
        """
        return cls(
            instance=instance,
            resource_uri=f'aws-rds://db-instance/{instance.get("DBInstanceIdentifier", "")}',
        )


@register_mcp_primitive_by_context(
    resource_params={
        'uri': 'aws-rds://db-instance/{instance_id}',
        'name': 'DescribeDBInstanceDetails',
        'mime_type': 'application/json',
        'description': DESCRIBE_INSTANCE_DETAIL_DOCSTRING,
    },
    tool_params={
        'name': 'DescribeDBInstanceDetails',
        'description': DESCRIBE_INSTANCE_DETAIL_DOCSTRING,
    },
)
@handle_exceptions
async def describe_instance_detail(
    instance_id: str = Field(..., description='The instance identifier'),
) -> Instance:
    """Get detailed information about a specific instance as a resource.

    Args:
        instance_id: The unique identifier of the RDS instance

    Returns:
        Instance: Detailed information about the specified RDS instance

    Raises:
        ValueError: If the specified instance is not found
    """
    logger.info(f'Getting instance detail resource for {instance_id}')
    rds_client = RDSConnectionManager.get_connection()

    response = await asyncio.to_thread(
        rds_client.describe_db_instances, DBInstanceIdentifier=instance_id
    )

    instances = response.get('DBInstances', [])
    if not instances:
        raise ValueError(f'Instance {instance_id} not found')

    return Instance.from_DBInstanceTypeDef(instances[0])
