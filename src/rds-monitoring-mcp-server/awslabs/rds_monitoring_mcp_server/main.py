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

"""awslabs RDS Monitoring MCP Server implementation."""

import argparse
from awslabs.rds_monitoring_mcp_server.common.constants import MCP_SERVER_VERSION
from awslabs.rds_monitoring_mcp_server.common.server import mcp
from awslabs.rds_monitoring_mcp_server.context import Context
from loguru import logger


def main():
    """Run the MCP server with CLI argument support."""
    parser = argparse.ArgumentParser(
        description='An AWS Labs MCP server for Amazon RDS Monitoring operations'
    )

    parser.add_argument('--port', type=int, default=8888, help='Port to run the server on')
    parser.add_argument(
        '--max-items',
        type=int,
        default=100,
        help='The maximum number of items (logs, reports, etc.) to retrieve',
    )
    parser.add_argument(
        '--readonly',
        default='true',
        action=argparse.BooleanOptionalAction,
        help='Prevents the MCP server from performing mutating operations',
    )
    parser.add_argument(
        '--register-resources-as-tools',
        action='store_true',
        help='Register resources as tools for MCP clients that do not support resources',
    )

    args = parser.parse_args()

    mcp.settings.port = args.port
    Context.initialize(args.readonly, args.max_items, args.register_resources_as_tools)

    # Import resources and tools for side effects to register them, this is done after Context has been initialized
    import awslabs.rds_monitoring_mcp_server.resources  # noqa: F401
    import awslabs.rds_monitoring_mcp_server.tools  # noqa: F401

    logger.info(f'Starting RDS Monitoring Plane MCP Server v{MCP_SERVER_VERSION}')

    # default streamable HTTP transport
    mcp.run()


if __name__ == '__main__':
    main()
