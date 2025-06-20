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

"""Tests for the discovery module of the rds-monitoring-mcp-server."""

import pytest
from awslabs.rds_monitoring_mcp_server.models import (
    ClusterOverview,
    InstanceOverview,
)
from awslabs.rds_monitoring_mcp_server.monitoring.discovery import (
    get_cluster_overview,
    get_instance_overview,
    list_clusters,
    list_instances,
)
from tests.test_constants import MOCK_DB_CLUSTERS_RESPONSE, MOCK_DB_INSTANCES_RESPONSE
from unittest.mock import MagicMock


class TestGetInstanceOverview:
    """Tests for the get_instance_overview function."""

    def test_get_instance_overview_complete(self):
        """Test extracting instance overview with complete data."""
        mock_instance = MOCK_DB_INSTANCES_RESPONSE['DBInstances'][0]

        result = get_instance_overview(mock_instance)

        assert isinstance(result, InstanceOverview)
        assert result.db_instance_identifier == 'example-postgres-instance'
        assert result.dbi_resource_id == 'db-EXAMPLE1234567890ABCDEFG'
        assert result.db_instance_status == 'available'
        assert result.db_instance_class == 'db.r6g.large'
        assert result.engine == 'aurora-postgresql'
        assert result.availability_zone == 'us-east-1a'
        assert result.multi_az is False
        assert len(result.tag_list) == 0


class TestGetClusterOverview:
    """Tests for the get_cluster_overview function."""

    def test_get_cluster_overview_complete(self):
        """Test extracting cluster overview with complete data."""
        mock_cluster = MOCK_DB_CLUSTERS_RESPONSE['DBClusters'][0]

        result = get_cluster_overview(mock_cluster)

        assert isinstance(result, ClusterOverview)
        assert result.db_cluster_identifier == 'example-postgres-cluster'
        assert result.db_cluster_resource_id == 'cluster-ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        assert result.status == 'available'
        assert result.engine == 'aurora-postgresql'
        assert result.multi_az is False
        assert len(result.tag_list) == 0


class TestListInstances:
    """Tests for the list_instances function."""

    @pytest.mark.asyncio
    async def test_list_instances(self):
        """Test retrieving a list of RDS instances."""
        mock_rds_client = MagicMock()
        paginator = MagicMock()
        paginator.paginate.return_value = [MOCK_DB_INSTANCES_RESPONSE]
        mock_rds_client.get_paginator.return_value = paginator

        result = await list_instances(mock_rds_client)

        assert len(result) == 3
        assert isinstance(result[0], InstanceOverview)
        assert isinstance(result[1], InstanceOverview)
        assert isinstance(result[2], InstanceOverview)
        assert result[0].db_instance_identifier == 'example-postgres-instance'
        assert result[1].db_instance_identifier == 'example-mysql-db'
        assert result[2].db_instance_identifier == 'example-db-1'
        assert result[0].engine == 'aurora-postgresql'
        assert result[1].engine == 'mysql'
        assert result[2].engine == 'mysql'

        mock_rds_client.get_paginator.assert_called_once_with('describe_db_instances')
        paginator.paginate.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_instances_empty(self):
        """Test retrieving a list of RDS instances when none exist."""
        mock_rds_client = MagicMock()
        paginator = MagicMock()
        paginator.paginate.return_value = [{'DBInstances': []}]
        mock_rds_client.get_paginator.return_value = paginator

        result = await list_instances(mock_rds_client)

        assert len(result) == 0

        mock_rds_client.get_paginator.assert_called_once_with('describe_db_instances')
        paginator.paginate.assert_called_once()


class TestListClusters:
    """Tests for the list_clusters function."""

    @pytest.mark.asyncio
    async def test_list_clusters(self):
        """Test retrieving a list of RDS clusters."""
        mock_rds_client = MagicMock()
        paginator = MagicMock()
        paginator.paginate.return_value = [MOCK_DB_CLUSTERS_RESPONSE]
        mock_rds_client.get_paginator.return_value = paginator

        result = await list_clusters(mock_rds_client)

        assert len(result) == 1
        assert isinstance(result[0], ClusterOverview)
        assert result[0].db_cluster_identifier == 'example-postgres-cluster'
        assert result[0].db_cluster_resource_id == 'cluster-ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        assert result[0].status == 'available'
        assert result[0].engine == 'aurora-postgresql'
        assert result[0].multi_az is False

        mock_rds_client.get_paginator.assert_called_once_with('describe_db_clusters')
        paginator.paginate.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_clusters_empty(self):
        """Test retrieving a list of RDS clusters when none exist."""
        mock_rds_client = MagicMock()
        paginator = MagicMock()
        paginator.paginate.return_value = [{'DBClusters': []}]
        mock_rds_client.get_paginator.return_value = paginator

        result = await list_clusters(mock_rds_client)

        assert len(result) == 0

        mock_rds_client.get_paginator.assert_called_once_with('describe_db_clusters')
        paginator.paginate.assert_called_once()
