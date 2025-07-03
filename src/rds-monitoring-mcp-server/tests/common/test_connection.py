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

"""Unit tests for connection management."""

import os
import pytest
from awslabs.rds_monitoring_mcp_server.common.connection import (
    CloudwatchConnectionManager,
    PIConnectionManager,
    RDSConnectionManager,
)
from botocore.config import Config
from unittest.mock import MagicMock, patch


CONNECTION_MANAGERS = [RDSConnectionManager, CloudwatchConnectionManager, PIConnectionManager]


@pytest.fixture(autouse=True)
def reset_connection():
    """Reset the connection before and after each test."""
    for manager in CONNECTION_MANAGERS:
        manager._client = None
    yield
    for manager in CONNECTION_MANAGERS:
        manager._client = None


@pytest.mark.parametrize('conn_manager', CONNECTION_MANAGERS)
def test_get_connection_default_settings(conn_manager):
    """Test connection creation with default settings."""
    with patch('boto3.Session') as mock_session:
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client

        client = conn_manager.get_connection()

        mock_session.assert_called_once_with(profile_name='default', region_name='us-east-1')
        mock_session.return_value.client.assert_called_once()

        client_args = mock_session.return_value.client.call_args[1]
        assert client_args['service_name'] == conn_manager._service_name
        config = client_args['config']
        assert isinstance(config, Config)

        assert client == mock_client


@pytest.mark.parametrize('conn_manager', CONNECTION_MANAGERS)
def test_get_connection_custom_settings(conn_manager):
    """Test connection creation with custom environment settings."""
    env_vars = {
        'AWS_PROFILE': 'test-profile',
        'AWS_REGION': 'us-west-2',
    }

    with patch.dict(os.environ, env_vars), patch('boto3.Session') as mock_session:
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client

        client = conn_manager.get_connection()

        mock_session.assert_called_once_with(profile_name='test-profile', region_name='us-west-2')
        mock_session.return_value.client.assert_called_once()

        assert client == mock_client


@pytest.mark.parametrize('conn_manager', CONNECTION_MANAGERS)
def test_connection_reuse(conn_manager):
    """Test that the connection is reused rather than recreated."""
    with patch('boto3.Session') as mock_session:
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client

        client1 = conn_manager.get_connection()
        client2 = conn_manager.get_connection()

        mock_session.assert_called_once()
        assert client1 == client2


@pytest.mark.parametrize('conn_manager', CONNECTION_MANAGERS)
def test_close_connection(conn_manager):
    """Test that close_connection properly closes and clears the client."""
    with patch('boto3.Session') as mock_session:
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client

        conn_manager.get_connection()
        conn_manager.close_connection()

        mock_client.close.assert_called_once()
        assert conn_manager._client is None


@pytest.mark.parametrize('conn_manager', CONNECTION_MANAGERS)
def test_close_connection_no_client(conn_manager):
    """Test close_connection when no client exists."""
    conn_manager.close_connection()
    assert conn_manager._client is None


@pytest.mark.parametrize('conn_manager', CONNECTION_MANAGERS)
def test_get_connection_after_close(conn_manager):
    """Test getting a new connection after closing the previous one."""
    with patch('boto3.Session') as mock_session:
        mock_client1 = MagicMock()
        mock_client2 = MagicMock()
        mock_session.return_value.client.side_effect = [mock_client1, mock_client2]

        client1 = conn_manager.get_connection()
        assert client1 == mock_client1

        conn_manager.close_connection()

        client2 = conn_manager.get_connection()
        assert client2 == mock_client2
        assert client1 != client2

        assert mock_session.call_count == 2
