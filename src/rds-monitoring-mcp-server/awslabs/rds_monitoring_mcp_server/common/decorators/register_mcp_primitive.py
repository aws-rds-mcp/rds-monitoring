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

from ..context import RDSContext
from ..server import mcp


def register_mcp_primitive_by_context(resource_params, tool_params):
    """Decorator to conditionally register as MCP resource or tool based on context.

    Args:
        resource_params: Parameters for @mcp.resource decorator
        tool_params: Parameters for @mcp.tool decorator
    """

    def decorator(func):
        if RDSContext.register_resource_as_tool():
            return mcp.tool(**tool_params)(func)
        else:
            return mcp.resource(**resource_params)(func)

    return decorator
