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

"""Tests for the rate_limiter decorator."""

import pytest
from awslabs.rds_monitoring_mcp_server.common.decorators.rate_limit import rate_limiter
from collections import defaultdict, deque
from unittest.mock import patch


@pytest.fixture
def clean_call_times():
    """Fixture to provide clean call times for each test."""
    with patch(
        'awslabs.rds_monitoring_mcp_server.common.decorators.rate_limit._call_times',
        defaultdict(deque),
    ):
        yield


class TestRateLimiter:
    """Tests for the rate_limiter decorator."""

    @pytest.mark.asyncio
    async def test_allows_calls_within_limit(self, clean_call_times):
        """Test that rate limiter allows calls within the limit."""

        @rate_limiter
        async def test_func():
            return 'success'

        for _ in range(3):
            result = await test_func()
            assert result == 'success'

    @pytest.mark.asyncio
    async def test_blocks_calls_over_limit(self, clean_call_times):
        """Test that rate limiter blocks calls over the limit."""

        @rate_limiter
        async def test_func():
            return 'success'

        for _ in range(3):
            await test_func()

        with pytest.raises(
            Exception, match='Rate limit exceeded.*test_func.*3 times per 50 seconds'
        ):
            await test_func()

    @pytest.mark.asyncio
    async def test_cleans_up_expired_calls(self):
        """Test that rate limiter cleans up expired calls."""
        with patch(
            'awslabs.rds_monitoring_mcp_server.common.decorators.rate_limit._call_times',
            defaultdict(deque),
        ):
            with patch('time.time') as mock_time:

                @rate_limiter
                async def test_func():
                    return 'success'

                mock_time.return_value = 1000.0
                for _ in range(3):
                    await test_func()

                mock_time.return_value = 1051.0
                result = await test_func()
                assert result == 'success'

    @pytest.mark.asyncio
    async def test_preserves_function_metadata(self):
        """Test that rate limiter preserves function metadata."""

        @rate_limiter
        async def test_func():
            """Test docstring."""
            return 'success'

        assert test_func.__name__ == 'test_func'
        assert test_func.__doc__ == 'Test docstring.'

    @pytest.mark.asyncio
    async def test_handles_function_arguments(self, clean_call_times):
        """Test that rate limiter handles function arguments."""

        @rate_limiter
        async def test_func(arg1, arg2, kwarg1=None):
            return f'{arg1}-{arg2}-{kwarg1}'

        result = await test_func('a', 'b', kwarg1='c')
        assert result == 'a-b-c'

    @pytest.mark.asyncio
    async def test_tracks_functions_separately(self, clean_call_times):
        """Test that rate limiter tracks different functions separately."""

        @rate_limiter
        async def func1():
            return 'func1'

        @rate_limiter
        async def func2():
            return 'func2'

        for _ in range(3):
            await func1()
            await func2()

        with pytest.raises(Exception):
            await func1()
        with pytest.raises(Exception):
            await func2()
