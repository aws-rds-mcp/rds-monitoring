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

"""aws-rds://metrics_guide resource implementation."""

from ...common.decorators import handle_exceptions
from ...common.server import mcp
from loguru import logger
from pathlib import Path


# Helper Funcs


def load_markdown_file(filename: str) -> str:
    """Load a markdown file from the static/react directory.

    Args:
        filename (str): The name of the markdown file to load (e.g. 'basic-ui-setup.md')

    Returns:
        str: The content of the markdown file, or empty string if file not found
    """
    base_dir = Path(__file__).parent.parent
    static_dir = base_dir / 'static'
    file_path = static_dir / filename

    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            logger.info(f'Loading markdown file: {file_path}')
            return f.read()
    else:
        logger.error('File not found: {file_path}')
        return f'Warning: File not found: {file_path}'


# MCP Resource Args

RESOURCE_DESCRIPTION = """Provide a link to the Amazon RDS Metrics Guide.

    <use_case>
    Use this resource to access the comprehensive Amazon RDS Metrics Guide for understanding RDS monitoring capabilities,
    metrics definitions, and best practices. This guide covers CloudWatch metrics, Performance Insights, Enhanced
    Monitoring, wait events, database logs, events and notifications, and recommendations for all RDS database engines.
    </use_case>

    <important_notes>
    1. The guide provides documentation links for detailed information on each metric type
    2. Metrics are organized by category (CloudWatch, Performance Insights, Enhanced Monitoring, etc.)
    3. Engine-specific metrics and wait events are included for MySQL, PostgreSQL, and Aurora variants
    4. Integration points with other AWS services like CloudWatch and EventBridge are documented
    5. Best practices for monitoring different database engines are provided
    </important_notes>
    """


@mcp.resource(
    uri='aws-rds://metrics_guide',
    name='RDSMetricGuide',
    description=RESOURCE_DESCRIPTION,
    mime_type='text/plain',
)
@handle_exceptions
async def metrics_guide_resource() -> str:
    """Serve the Amazon RDS Metrics Guide markdown file.

    This function returns the content of the comprehensive RDS metrics guide, which includes:
    - CloudWatch metrics for instances, clusters, and global databases
    - Performance Insights metrics and dimensions for load analysis
    - Wait events for different database engines (MySQL, PostgreSQL, Aurora)
    - Enhanced Monitoring operating system metrics
    - Database log types and access methods
    - Events and notifications
    - Recommendations and advisor tools
    - Integration with other AWS services
    - Monitoring best practices

    Returns:
        str: The markdown content of the RDS metrics guide
    """
    return load_markdown_file('metrics_guide.md')
