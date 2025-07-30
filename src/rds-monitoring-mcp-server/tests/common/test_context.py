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

"""Tests for the RDSContext class."""

import pytest
from awslabs.rds_monitoring_mcp_server.common.context import RDSContext


@pytest.fixture(autouse=True)
def reset_RDSContext():
    """Reset the RDSContext class to default values after each test."""
    yield
    RDSContext.initialize(readonly=True, max_items=100)


def test_default_values():
    """Test that the default values are set correctly."""
    assert RDSContext._readonly is True
    assert RDSContext._max_items == 100


def test_initialize():
    """Test that the initialize method correctly updates class variables."""
    RDSContext.initialize(readonly=False, max_items=200)
    assert RDSContext._readonly is False
    assert RDSContext._max_items == 200

    # Test with just readonly parameter
    RDSContext.initialize(readonly=True, max_items=100)
    assert RDSContext._readonly is True
    assert RDSContext._max_items == 100

    # Test with just max_items parameter
    RDSContext.initialize(readonly=True, max_items=300)
    assert RDSContext._readonly is True
    assert RDSContext._max_items == 300


def test_readonly_mode():
    """Test that the readonly_mode method returns the correct value."""
    RDSContext._readonly = True
    assert RDSContext.readonly_mode() is True

    RDSContext._readonly = False
    assert RDSContext.readonly_mode() is False


def test_max_items():
    """Test that the max_items method returns the correct value."""
    RDSContext._max_items = 100
    assert RDSContext.max_items() == 100

    RDSContext._max_items = 200
    assert RDSContext.max_items() == 200


def test_get_pagination_config():
    """Test that the get_pagination_config method returns the expected dictionary."""
    RDSContext._max_items = 100
    expected = {
        'MaxItems': 100,
    }
    assert RDSContext.get_pagination_config() == expected

    RDSContext._max_items = 200
    expected = {
        'MaxItems': 200,
    }
    assert RDSContext.get_pagination_config() == expected
