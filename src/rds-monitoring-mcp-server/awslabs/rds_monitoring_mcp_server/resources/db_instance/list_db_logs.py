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

"""aws-rds://db-instance/{db_instance_identifier}/log data models and resource implementation."""

from ...common.connection import RDSConnectionManager
from ...common.context import RDSContext
from ...common.decorators.handle_exceptions import handle_exceptions
from ...common.decorators.register_mcp_primitive import register_mcp_primitive_by_context
from ...common.utils import handle_paginated_aws_api_call
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List


RESOURCE_DESCRIPTION = """List all available NON-EMPTY log files for a specific Amazon RDS instance.

This resource retrieves information about non-empty log files for a specific RDS database instance, which provide detailed logs of database activities for troubleshooting issues and monitoring performance.
"""


class DBLogFileSummary(BaseModel):
    """Database log file information.

    This model represents an Amazon RDS database log file with its metadata,
    including name, last modification time, and size.

    Attributes:
        log_file_name: The name of the log file in the database instance.
        last_written: A POSIX timestamp when the last log entry was written.
        size: Size of the log file in bytes.
    """

    log_file_name: str = Field(
        description='Name of the log file',
    )
    last_written: datetime = Field(
        description='A POSIX timestamp when the last log entry was written.'
    )
    size: int = Field(description='Size of the log file in bytes', ge=0)


class DBLogFileListModel(BaseModel):
    """DB cluster list model."""

    log_files: List[DBLogFileSummary] = Field(
        default_factory=list, description='List of DB log files'
    )
    count: int = Field(
        description='Total number of non-empty log files for the DB instance in Amazon RDS'
    )


resource_params = {
    'uri': 'aws-rds://db-instance/{db_instance_identifier}/log',
    'name': 'ListDBLogFiles',
    'mime_type': 'application/json',
    'description': RESOURCE_DESCRIPTION,
}

tool_params = {
    'name': 'ListDBLogFiles',
    'description': RESOURCE_DESCRIPTION,
}


@register_mcp_primitive_by_context(resource_params, tool_params)
@handle_exceptions
def list_db_log_files(
    db_instance_identifier: str = Field(..., description='The identifier for the DB instance'),
) -> DBLogFileListModel:
    """List all non-empty log files for the database.

    Args:
        db_instance_identifier: The identifier of the DB instance.

    Returns:
        JSON string containing a list of DBLogFileOverview objects representing non-empty log files.
    """
    rds_client = RDSConnectionManager.get_connection()

    operation_parameters = {
        'DBInstanceIdentifier': db_instance_identifier,
        'FileSize': 1,
        'PaginationConfig': RDSContext.get_pagination_config(),
    }

    log_files = handle_paginated_aws_api_call(
        client=rds_client,
        paginator_name='describe_db_log_files',
        operation_parameters=operation_parameters,
        format_function=lambda log_file: DBLogFileSummary(
            log_file_name=log_file.get('LogFileName', ''),
            last_written=datetime.fromtimestamp(log_file.get('LastWritten', 0) / 1000),
            size=log_file.get('Size', 0),
        ),
        result_key='DescribeDBLogFiles',
    )

    result = DBLogFileListModel(
        log_files=log_files,
        count=len(log_files),
    )

    return result
