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

"""Rate limiting decorator for function calls."""

import time
from collections import defaultdict, deque
from functools import wraps
from typing import Any, Callable


CALLS_PER_PERIOD_LIMIT = 3
PERIOD = 50

_call_times = defaultdict(lambda: deque(maxlen=CALLS_PER_PERIOD_LIMIT))


def rate_limiter(func: Callable) -> Callable:
    """Decorator to limit function calls to CALLS_PER_PERIOD_LIMIT times per PERIOD seconds.

    Raises:
        Exception: When rate limit is exceeded
    """

    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        current_time = time.time()
        func_name = func.__name__

        while _call_times[func_name] and current_time - _call_times[func_name][0] >= PERIOD:
            _call_times[func_name].popleft()

        if len(_call_times[func_name]) >= CALLS_PER_PERIOD_LIMIT:
            raise Exception(
                f'Rate limit exceeded: {func_name} can only be called {CALLS_PER_PERIOD_LIMIT} times per {PERIOD} seconds. Please wait before retrying.'
            )

        _call_times[func_name].append(current_time)
        return await func(*args, **kwargs)

    return wrapper
