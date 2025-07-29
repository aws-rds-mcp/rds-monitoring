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

"""Utility functions for the RDS Monitoring MCP Server."""

from .context import RDSContext
from botocore.client import BaseClient
from datetime import datetime
from loguru import logger
from typing import Any, Callable, Dict, List, Optional, TypeVar


T = TypeVar('T', bound=object)


def handle_paginated_aws_api_call(
    client: BaseClient,
    paginator_name: str,
    operation_parameters: Dict[str, Any],
    result_key: str,
    format_function: Optional[Callable[[Any], T]] = None,
) -> List[Any]:
    """Fetch all results using AWS API pagination.

    Args:
        client: Boto3 client to use for the API call
        paginator_name: Name of the paginator to use (e.g. 'describe_db_clusters')
        operation_parameters: Parameters to pass to the paginator
        result_key: Key in the response that contains the list of items
        format_function: Optional function to format each item in the result. If None, raw items are returned.

    Returns:
        List of results, either formatted or raw depending on format_function
    """
    results = []
    paginator = client.get_paginator(paginator_name)
    operation_parameters['PaginationConfig'] = RDSContext.get_pagination_config()
    page_iterator = paginator.paginate(**operation_parameters)
    for page in page_iterator:
        for item in page.get(result_key, []):
            if format_function:
                results.append(format_function(item))
            else:
                results.append(item)

    return results


def convert_datetime_to_string(obj: Any) -> Any:
    """Recursively convert datetime objects to ISO format strings.

    Args:
        obj: Object to convert

    Returns:
        Object with datetime objects converted to strings
    """
    import datetime

    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: convert_datetime_to_string(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_datetime_to_string(item) for item in obj]
    return obj


def convert_string_to_datetime(default: datetime, date_string: Optional[str] = None) -> datetime:
    """Convert date strings to datetime objects.

    Handles multiple date formats and provides robust error handling.

    Args:
        default: The default date to fallback on if parsing fails
        date_string: Date string in ISO format or other common formats

    Returns:
        A datetime object

    Raises:
        ValueError: If the date strings are provided but cannot be parsed
    """
    import re
    from datetime import datetime

    def parse_date_string(default: datetime, date_str: Optional[str] = None) -> datetime:
        if not date_str:
            return default

        # Handle common formats
        try:
            # Try ISO format with Z (UTC) suffix
            if date_str.endswith('Z'):
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))

            # Try ISO format directly
            if 'T' in date_str or '-' in date_str:
                return datetime.fromisoformat(date_str)

            # Try simple YYYY-MM-DD format
            if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                return datetime.strptime(date_str, '%Y-%m-%d')

            # Try MM/DD/YYYY format
            if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', date_str):
                return datetime.strptime(date_str, '%m/%d/%Y')

            # Try Unix timestamp (seconds since epoch)
            if date_str.isdigit():
                return datetime.fromtimestamp(int(date_str))

            # Default case if no format matches
            return default

        except ValueError as e:
            raise ValueError(f"Invalid date format '{date_str}': {str(e)}")

    try:
        return parse_date_string(default, date_string)
    except ValueError as e:
        logger.warning(f"Error parsing end_date '{date_string}': {str(e)}. Using default value.")
        return default
