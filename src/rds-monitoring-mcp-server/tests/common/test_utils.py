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

"""Tests for the utilities in utils.py."""

from awslabs.rds_monitoring_mcp_server.common.utils import (
    convert_datetime_to_string,
    convert_string_to_datetime,
)
from datetime import datetime


class TestConvertDatetimeToString:
    """Tests for convert_datetime_to_string function."""

    def test_convert_simple_datetime(self):
        """Test converting a simple datetime object."""
        test_date = datetime(2025, 6, 15, 10, 30, 45)
        result = convert_datetime_to_string(test_date)
        assert result == test_date.isoformat()
        assert isinstance(result, str)

    def test_convert_dict_with_datetime(self):
        """Test converting a dictionary with datetime values."""
        test_dict = {
            'created_at': datetime(2025, 6, 15, 10, 30, 45),
            'name': 'test-resource',
            'updated_at': datetime(2025, 6, 16, 11, 0, 0),
        }
        result = convert_datetime_to_string(test_dict)

        assert isinstance(result, dict)
        assert result['created_at'] == datetime(2025, 6, 15, 10, 30, 45).isoformat()
        assert result['name'] == 'test-resource'
        assert result['updated_at'] == datetime(2025, 6, 16, 11, 0, 0).isoformat()

    def test_convert_list_with_datetime(self):
        """Test converting a list with datetime objects."""
        test_list = [
            datetime(2025, 6, 15, 10, 30, 45),
            'string-value',
            datetime(2025, 6, 16, 11, 0, 0),
        ]
        result = convert_datetime_to_string(test_list)

        assert isinstance(result, list)
        assert result[0] == datetime(2025, 6, 15, 10, 30, 45).isoformat()
        assert result[1] == 'string-value'
        assert result[2] == datetime(2025, 6, 16, 11, 0, 0).isoformat()

    def test_convert_nested_structure(self):
        """Test converting a nested structure with datetime objects."""
        nested_structure = {
            'metadata': {
                'created_at': datetime(2025, 6, 15, 10, 30, 45),
                'tags': ['test', 'example'],
            },
            'items': [
                {'id': 1, 'timestamp': datetime(2025, 6, 16, 11, 0, 0)},
                {'id': 2, 'timestamp': datetime(2025, 6, 17, 12, 15, 30)},
            ],
        }
        result = convert_datetime_to_string(nested_structure)

        assert isinstance(result, dict)
        assert result['metadata']['created_at'] == datetime(2025, 6, 15, 10, 30, 45).isoformat()
        assert result['metadata']['tags'] == ['test', 'example']
        assert result['items'][0]['timestamp'] == datetime(2025, 6, 16, 11, 0, 0).isoformat()
        assert result['items'][1]['timestamp'] == datetime(2025, 6, 17, 12, 15, 30).isoformat()

    def test_convert_non_datetime_objects(self):
        """Test that non-datetime objects remain unchanged."""
        test_obj = {
            'string': 'test',
            'number': 42,
            'boolean': True,
            'none': None,
            'list': [1, 2, 3],
        }
        result = convert_datetime_to_string(test_obj)
        assert result == test_obj


class TestConvertStringToDatetime:
    """Tests for convert_string_to_datetime function."""

    def test_none_value(self):
        """Test with None value returns the default."""
        default = datetime(2025, 6, 15, 10, 30, 45)
        result = convert_string_to_datetime(default, None)
        assert result == default

    def test_empty_string(self):
        """Test with empty string returns the default."""
        default = datetime(2025, 6, 15, 10, 30, 45)
        result = convert_string_to_datetime(default, '')
        assert result == default

    def test_iso_format(self):
        """Test parsing ISO format date string."""
        default = datetime(2025, 6, 15, 10, 30, 45)
        date_string = '2025-07-20T14:30:00'
        expected = datetime(2025, 7, 20, 14, 30, 0)
        result = convert_string_to_datetime(default, date_string)
        assert result == expected

    def test_iso_with_z_suffix(self):
        """Test parsing ISO format with Z (UTC) suffix."""
        default = datetime(2025, 6, 15, 10, 30, 45)
        date_string = '2025-07-20T14:30:00Z'
        expected = datetime.fromisoformat('2025-07-20T14:30:00+00:00')
        result = convert_string_to_datetime(default, date_string)
        assert result == expected

    def test_simple_date_format(self):
        """Test parsing simple YYYY-MM-DD format."""
        default = datetime(2025, 6, 15, 10, 30, 45)
        date_string = '2025-07-20'
        expected = datetime(2025, 7, 20, 0, 0, 0)
        result = convert_string_to_datetime(default, date_string)
        assert result == expected

    def test_mm_dd_yyyy_format(self):
        """Test parsing MM/DD/YYYY format."""
        default = datetime(2025, 6, 15, 10, 30, 45)
        date_string = '7/20/2025'
        expected = datetime(2025, 7, 20, 0, 0, 0)
        result = convert_string_to_datetime(default, date_string)
        assert result == expected

    def test_unix_timestamp(self):
        """Test parsing Unix timestamp format."""
        default = datetime(2025, 6, 15, 10, 30, 45)
        timestamp = '1716470400'
        result = convert_string_to_datetime(default, timestamp)
        assert isinstance(result, datetime)

    def test_invalid_format(self):
        """Test invalid date format returns the default value."""
        default = datetime(2025, 6, 15, 10, 30, 45)
        date_string = 'invalid-date-format'

        result = convert_string_to_datetime(default, date_string)
        assert result == default
