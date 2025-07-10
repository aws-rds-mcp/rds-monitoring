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

"""aws-rds://db-instance/{db_instance_identifier}/available_metrics data models and resource implementation."""

from ...common.decorators import conditional_mcp_register, handle_exceptions
from ...common.list_metrics import list_metrics
from typing import List


RESOURCE_DESCRIPTION = """List available metrics for a specific Amazon RDS instance.

    <use_case>
    Use this resource to discover all available CloudWatch metrics for a specific RDS database instance.
    These metrics provide insights into database performance, resource utilization, and operational health.
    </use_case>

    <important_notes>
    1. The response provides a complete list of available metrics specific to the instance
    2. The db_instance_identifier parameter must match an existing RDS instance
    3. Metrics are filtered to the AWS region specified in your environment configuration
    4. Use the `aws-rds://db-instance/{db_instance_identifier}/metrics/{metric_name}` resource to retrieve
       actual metric data for a specific metric
    5. The metrics returned include both standard CloudWatch metrics and enhanced monitoring metrics
       if enabled on the instance
    </important_notes>

    Args:
        db_instance_identifier: The identifier of the RDS instance to retrieve metrics for

    Returns:
        List[str]: A list of available metric names for the specified RDS instance

    <examples>
    Example usage scenarios:
    1. Performance monitoring setup:
       - Discover available metrics before setting up monitoring dashboards
       - Identify which metrics are available for specific database engines

    2. Alerting configuration:
       - Find relevant metrics for creating CloudWatch alarms
       - Determine appropriate metrics for different monitoring needs (CPU, memory, I/O)
    </examples>
    """


resource_params = {
    'uri': 'aws-rds://db-instance/{db_instance_identifier}/available_metrics',
    'name': 'ListRDSInstanceMetrics',
    'description': RESOURCE_DESCRIPTION,
    'mime_type': 'text/plain',
}

tool_params = {
    'name': 'ListRDSInstanceMetrics',
    'description': RESOURCE_DESCRIPTION,
}


@conditional_mcp_register(resource_params, tool_params)
@handle_exceptions
async def list_instance_metrics(db_instance_identifier: str) -> List[str]:
    """List available metrics for an Amazon RDS instance.

    This function retrieves a list of all available CloudWatch metrics for a specified
    RDS database instance. It uses the DB instance identifier to filter metrics specifically
    for that instance.

    Args:
        db_instance_identifier (str): The identifier of the RDS instance to retrieve metrics for.

    Returns:
        List[str]: A list of available metric names for the specified RDS instance.
    """
    return await list_metrics(
        dimension_name='DBInstanceIdentifier',
        dimension_value=db_instance_identifier,
    )
