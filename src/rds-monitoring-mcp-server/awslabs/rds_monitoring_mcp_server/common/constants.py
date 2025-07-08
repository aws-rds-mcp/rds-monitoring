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

"""Constants used across the Amazon RDS Monitoring MCP Server."""

# MCP Server Version
MCP_SERVER_VERSION = '0.1.0'

# A tag attached to any resources created by the MCP server
MCP_SERVER_TAGS = [
    {'Key': 'mcp_server_version', 'Value': MCP_SERVER_VERSION},
    {'Key': 'created_by', 'Value': 'rds-control-plane-mcp-server'},
]

# Error Messages
ERROR_AWS_API = 'AWS API error: {}'
ERROR_UNEXPECTED = 'Unexpected error: {}'
