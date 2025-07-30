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

"""Tests for the register_mcp_primitive decorator in the RDS Monitoring MCP Server."""

from awslabs.rds_monitoring_mcp_server.common.context import RDSContext
from awslabs.rds_monitoring_mcp_server.common.decorators.register_mcp_primitive import (
    register_mcp_primitive_by_context,
)
from unittest.mock import MagicMock, patch


def test_register_mcp_primitive_as_tool():
    """Test that the decorator registers as a tool when register_resource_as_tool is True."""
    resource_params = {
        'uri': 'aws-rds://test-resource',
        'name': 'TestResource',
        'description': 'Test resource',
        'mime_type': 'text/plain',
    }

    tool_params = {
        'name': 'TestTool',
        'description': 'Test tool',
    }

    def test_func():
        return 'test function'

    with patch.object(RDSContext, 'register_resource_as_tool', return_value=True):
        with patch(
            'awslabs.rds_monitoring_mcp_server.common.decorators.register_mcp_primitive.mcp'
        ) as mock_mcp:
            mock_tool = MagicMock(return_value=lambda f: f)
            mock_mcp.tool = mock_tool

            result = register_mcp_primitive_by_context(resource_params, tool_params)(test_func)

            mock_tool.assert_called_once_with(**tool_params)
            assert result == test_func


def test_register_mcp_primitive_as_resource():
    """Test that the decorator registers as a resource when register_resource_as_tool is False."""
    resource_params = {
        'uri': 'aws-rds://test-resource',
        'name': 'TestResource',
        'description': 'Test resource',
        'mime_type': 'text/plain',
    }

    tool_params = {
        'name': 'TestTool',
        'description': 'Test tool',
    }

    def test_func():
        return 'test function'

    with patch.object(RDSContext, 'register_resource_as_tool', return_value=False):
        with patch(
            'awslabs.rds_monitoring_mcp_server.common.decorators.register_mcp_primitive.mcp'
        ) as mock_mcp:
            mock_resource = MagicMock(return_value=lambda f: f)
            mock_mcp.resource = mock_resource

            result = register_mcp_primitive_by_context(resource_params, tool_params)(test_func)

            mock_resource.assert_called_once_with(**resource_params)
            assert result == test_func


def test_register_mcp_primitive_passes_function():
    """Test that the decorator correctly passes the decorated function to mcp decorators."""
    resource_params = {'uri': 'test://uri'}
    tool_params = {'name': 'TestTool'}

    def test_func():
        return 'original function'

    test_func.unique_attr = 'test attribute'

    with patch(
        'awslabs.rds_monitoring_mcp_server.common.decorators.register_mcp_primitive.mcp'
    ) as mock_mcp:
        mock_mcp.tool = lambda **kwargs: lambda f: f
        mock_mcp.resource = lambda **kwargs: lambda f: f

        with patch.object(RDSContext, 'register_resource_as_tool', return_value=True):
            decorated = register_mcp_primitive_by_context(resource_params, tool_params)(test_func)
            assert decorated == test_func
            assert hasattr(decorated, 'unique_attr')
            assert decorated.unique_attr == 'test attribute'

        with patch.object(RDSContext, 'register_resource_as_tool', return_value=False):
            decorated = register_mcp_primitive_by_context(resource_params, tool_params)(test_func)
            assert decorated == test_func
            assert hasattr(decorated, 'unique_attr')
            assert decorated.unique_attr == 'test attribute'
