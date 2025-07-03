from awslabs.rds_monitoring_mcp_server.resources.general.metrics_guide import (
    load_markdown_file,
)
from unittest.mock import mock_open, patch


class TestLoadMarkdownFile:
    """Tests for load_markdown_file function."""

    @patch('pathlib.Path.exists')
    @patch(
        'builtins.open',
        new_callable=mock_open,
        read_data='# Test Markdown\n\nThis is test content.',
    )
    def test_load_existing_file(self, mock_file, mock_exists):
        """Test loading an existing markdown file."""
        mock_exists.return_value = True
        result = load_markdown_file('test.md')

        assert result == '# Test Markdown\n\nThis is test content.'

        mock_exists.assert_called_once()
        mock_file.assert_called_once()

    @patch('pathlib.Path.exists')
    def test_load_nonexistent_file(self, mock_exists):
        """Test loading a non-existent markdown file."""
        mock_exists.return_value = False
        test_filename = 'nonexistent.md'
        result = load_markdown_file(test_filename)

        assert 'Warning: File not found' in result

        mock_exists.assert_called_once()
