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

"""Tests for the handle_exceptions decorator in the RDS Monitoring MCP Server."""

import json
import pytest
from awslabs.rds_monitoring_mcp_server.common.decorators.handle_exceptions import handle_exceptions
from botocore.exceptions import ClientError
from unittest.mock import patch


@pytest.mark.asyncio
async def test_handle_exceptions_success_async():
    """Test that the decorator passes through successful async function calls."""

    @handle_exceptions
    async def test_func():
        return 'success'

    result = await test_func()
    assert result == 'success'


@pytest.mark.asyncio
async def test_handle_exceptions_success_sync():
    """Test that the decorator passes through successful sync function calls."""

    @handle_exceptions
    def test_func():
        return 'success'

    result = await test_func()
    assert result == 'success'


@pytest.mark.asyncio
async def test_handle_exceptions_client_error():
    """Test that the decorator handles ClientError exceptions."""
    error_response = {
        'Error': {'Code': 'InvalidParameterValue', 'Message': 'Invalid parameter value'}
    }

    @handle_exceptions
    def test_func():
        raise ClientError(error_response, 'TestOperation')

    with patch('awslabs.rds_monitoring_mcp_server.common.decorators.handle_exceptions.logger'):
        result = await test_func()

    result_dict = json.loads(result)
    assert result_dict['error'] == 'AWS API error: InvalidParameterValue'
    assert result_dict['error_code'] == 'InvalidParameterValue'
    assert result_dict['error_message'] == 'Invalid parameter value'
    assert result_dict['operation'] == 'test_func'


@pytest.mark.asyncio
async def test_handle_exceptions_general_error():
    """Test that the decorator handles general exceptions."""

    @handle_exceptions
    def test_func():
        raise ValueError('Test error message')

    with patch('awslabs.rds_monitoring_mcp_server.common.decorators.handle_exceptions.logger'):
        result = await test_func()

    result_dict = json.loads(result)
    assert result_dict['error'] == 'Unexpected error: Test error message'
    assert result_dict['error_type'] == 'ValueError'
    assert result_dict['error_message'] == 'Test error message'
    assert result_dict['operation'] == 'test_func'


@pytest.mark.asyncio
async def test_handle_exceptions_with_args_kwargs():
    """Test that the decorator preserves function arguments."""

    @handle_exceptions
    def test_func(arg1, arg2, kwarg1=None):
        return f'{arg1}-{arg2}-{kwarg1}'

    result = await test_func('a', 'b', kwarg1='c')
    assert result == 'a-b-c'


@pytest.mark.asyncio
async def test_handle_exceptions_async_client_error():
    """Test that the decorator handles ClientError in async functions."""
    error_response = {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}}

    @handle_exceptions
    async def test_func():
        raise ClientError(error_response, 'AsyncTestOperation')

    with patch('awslabs.rds_monitoring_mcp_server.common.decorators.handle_exceptions.logger'):
        result = await test_func()

    result_dict = json.loads(result)
    assert result_dict['error'] == 'AWS API error: AccessDenied'
    assert result_dict['error_code'] == 'AccessDenied'
    assert result_dict['error_message'] == 'Access denied'
    assert result_dict['operation'] == 'test_func'
