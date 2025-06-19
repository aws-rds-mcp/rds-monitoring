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

"""Test fixtures for the rds-monitoring-mcp-server tests."""

import pytest
from .test_constants import MOCK_DB_CLUSTERS_RESPONSE, MOCK_DB_INSTANCES_RESPONSE
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_rds_client():
    """Create a mock RDS client."""
    client = MagicMock()
    client.meta.region_name = 'us-east-1'

    client.describe_db_instances.return_value = MOCK_DB_INSTANCES_RESPONSE
    client.describe_db_clusters.return_value = MOCK_DB_CLUSTERS_RESPONSE

    return client


@pytest.fixture
def mock_boto3():
    """Create a mock boto3 module."""
    with patch('boto3.client') as mock_client, patch('boto3.Session') as mock_session:
        mock_pi = MagicMock()
        mock_rds = MagicMock()
        mock_cloudwatch = MagicMock()

        mock_client.side_effect = lambda service, region_name=None: {
            'pi': mock_pi,
            'rds': mock_rds,
            'cloudwatch': mock_cloudwatch,
        }[service]

        mock_session_instance = MagicMock()
        mock_session_instance.client.side_effect = lambda service, region_name=None: {
            'pi': mock_pi,
            'rds': mock_rds,
            'cloudwatch': mock_cloudwatch,
        }[service]
        mock_session.return_value = mock_session_instance

        yield {
            'client': mock_client,
            'Session': mock_session,
            'pi': mock_pi,
            'rds': mock_rds,
            'cloudwatch': mock_cloudwatch,
        }
