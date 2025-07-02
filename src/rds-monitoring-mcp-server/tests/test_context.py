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

"""Tests for the Context class."""

import pytest
from awslabs.rds_monitoring_mcp_server.context import Context


@pytest.fixture(autouse=True)
def reset_context():
    """Reset the Context class to default values after each test."""
    yield
    Context.initialize(readonly=True, max_items=100)


def test_default_values():
    """Test that the default values are set correctly."""
    assert Context._readonly is True
    assert Context._max_items == 100


def test_initialize():
    """Test that the initialize method correctly updates class variables."""
    Context.initialize(readonly=False, max_items=200)
    assert Context._readonly is False
    assert Context._max_items == 200

    # Test with just readonly parameter
    Context.initialize(readonly=True, max_items=100)
    assert Context._readonly is True
    assert Context._max_items == 100

    # Test with just max_items parameter
    Context.initialize(readonly=True, max_items=300)
    assert Context._readonly is True
    assert Context._max_items == 300


def test_readonly_mode():
    """Test that the readonly_mode method returns the correct value."""
    Context._readonly = True
    assert Context.readonly_mode() is True

    Context._readonly = False
    assert Context.readonly_mode() is False


def test_max_items():
    """Test that the max_items method returns the correct value."""
    Context._max_items = 100
    assert Context.max_items() == 100

    Context._max_items = 200
    assert Context.max_items() == 200


def test_get_pagination_config():
    """Test that the get_pagination_config method returns the expected dictionary."""
    Context._max_items = 100
    expected = {
        'MaxItems': 100,
        'PageSize': 20,
    }
    assert Context.get_pagination_config() == expected

    Context._max_items = 200
    expected = {
        'MaxItems': 200,
        'PageSize': 20,
    }
    assert Context.get_pagination_config() == expected
