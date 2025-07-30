# AWS RDS Monitoring MCP Server

An AWS Labs Model Context Protocol (MCP) server for monitoring and analyzing Amazon RDS database instances and clusters. This server provides comprehensive tools and resources for RDS performance monitoring, log analysis, and troubleshooting.

## Available Resource Templates

### DB Cluster Resources
- `aws-rds://db-cluster` - List all available Amazon RDS clusters in your account
- `aws-rds://db-cluster/{cluster_id}` - Get detailed information about a specific RDS cluster

### DB Instance Resources
- `aws-rds://db-instance` - List all available Amazon RDS instances in your account
- `aws-rds://db-instance/{instance_id}` - Get detailed information about a specific RDS instance
- `aws-rds://db-instance/{dbi_resource_identifier}/log` - List all available non-empty log files for a specific RDS instance
- `aws-rds://db-instance/{dbi_resource_identifier}/performance_report` - List all available performance reports for a specific RDS instance
- `aws-rds://db-instance/{dbi_resource_identifier}/performance_report/{report_id}` - Read a specific performance report

### General Resources
- `aws-rds://{resource_type}/{resource_identifier}/cloudwatch_metrics` - List available metrics for a RDS resource (db-instance or db-cluster)
- `aws-rds://metrics-guide` - Access the comprehensive Amazon RDS Metrics Guide

## Available Tools

### General Monitoring Tools

- **DescribeRDSEvents** - List events for RDS resources (instances, clusters, snapshots, etc.) with filtering by category, time period, and source type
- **DescribeRDSPerformanceMetrics** - Retrieve performance metrics for RDS resources including instances, clusters, and global clusters
- **DescribeRDSRecommendations** - Get RDS recommendations for operational improvements, performance enhancements, and best practices

### DB Instance Performance Tools

- **FindSlowQueriesAndWaitEvents** - Identify slow SQL queries and wait events causing performance bottlenecks using Performance Insights
- **ReadDBLogFiles** - Read and analyze database log files from RDS instances with pattern filtering and pagination
- **CreatePerformanceReport** - Generate comprehensive performance analysis reports for RDS instances over specified time periods

## Instructions

The AWS RDS Monitoring MCP Server provides specialized tools for monitoring, analyzing, and troubleshooting Amazon RDS database performance. This server focuses on read-only monitoring operations and does not include database management or modification capabilities.

Key features:
- **Performance Insights Integration**: Analyze slow queries and wait events
- **Log File Analysis**: Read and filter database logs
- **Metrics and Events**: Access CloudWatch metrics and RDS events
- **Performance Reports**: Generate detailed performance analysis reports
- **Recommendations**: Get AWS recommendations for optimization

To use these tools, ensure you have proper AWS credentials configured with appropriate permissions for RDS monitoring operations. The server will automatically use credentials from environment variables or other standard AWS credential sources.

## Prerequisites

1. Install `uv` from [Astral](https://docs.astral.sh/uv/getting-started/installation/) or the [GitHub README](https://github.com/astral-sh/uv#installation)
2. Install Python using `uv python install 3.10`
3. Set up AWS credentials with access to RDS monitoring services:
   - `rds:DescribeDBInstances`
   - `rds:DescribeDBClusters`
   - `rds:DescribeEvents`
   - `rds:DescribeDBLogFiles`
   - `rds:DownloadDBLogFilePortion`
   - `pi:GetResourceMetrics` (for Performance Insights)
   - `pi:DescribeDimensionKeys`
   - `pi:GetDimensionKeyDetails`
   - `cloudwatch:GetMetricStatistics`
   - `support:DescribeTrustedAdvisorChecks` (for recommendations)

## Installation

Add the MCP server to your favorite agentic tools (e.g., for Amazon Q Developer CLI MCP, `~/.aws/amazonq/mcp.json`):

```json
{
  "mcpServers": {
    "awslabs.rds-monitoring-mcp-server": {
      "command": "uvx",
      "args": ["awslabs.rds-monitoring-mcp-server@latest"],
      "env": {
        "AWS_PROFILE": "default",
        "AWS_REGION": "us-west-2",
        "FASTMCP_LOG_LEVEL": "ERROR"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

For read-only mode (recommended for monitoring):

```json
{
  "mcpServers": {
    "awslabs.rds-monitoring-mcp-server": {
      "command": "uvx",
      "args": [
        "awslabs.rds-monitoring-mcp-server@latest",
        "--readonly"
      ],
      "env": {
        "AWS_PROFILE": "default",
        "AWS_REGION": "us-west-2",
        "FASTMCP_LOG_LEVEL": "ERROR"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

Using Docker after building with `docker build -t awslabs/rds-monitoring-mcp-server .`:

```json
{
  "mcpServers": {
    "awslabs.rds-monitoring-mcp-server": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "--interactive",
        "--env",
        "FASTMCP_LOG_LEVEL=ERROR",
        "awslabs/rds-monitoring-mcp-server:latest",
        "--readonly"
      ],
      "env": {},
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

## Configuration

### AWS Configuration

Configure AWS credentials and region:

```bash
# AWS settings
AWS_PROFILE=default              # AWS credential profile to use
AWS_REGION=us-east-1             # AWS region to connect to
```

The server automatically handles:
- AWS authentication and credential management
- Connection establishment for RDS, Performance Insights, and CloudWatch

### Server Settings

The following CLI arguments can be passed when running the server:

```bash
# Server CLI arguments
--max-items 100                          # Maximum number of items returned from API responses
--port 8888                              # Port to run the server on
--readonly                               # Run in readonly mode (default: true)
--no-readonly                            # Allow mutating operations (not recommended for monitoring)
--register-resources-as-tools            # Register resources as tools for MCP clients that don't support resources
```

Example configuration with custom settings:

```json
{
  "mcpServers": {
    "awslabs.rds-monitoring-mcp-server": {
      "command": "uvx",
      "args": [
        "awslabs.rds-monitoring-mcp-server@latest",
        "--readonly",
        "--max-items", "50",
        "--port", "8889"
      ],
      "env": {
        "AWS_PROFILE": "monitoring",
        "AWS_REGION": "us-east-1",
        "FASTMCP_LOG_LEVEL": "INFO"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

## Usage Examples

### Performance Troubleshooting
1. Use `FindSlowQueriesAndWaitEvents` to identify performance bottlenecks
2. Use `ReadDBLogFiles` to analyze error logs for specific time periods
3. Use `DescribeRDSPerformanceMetrics` to get CloudWatch metrics
4. Use `CreatePerformanceReport` for comprehensive analysis

### Monitoring Workflows
1. List instances with `aws-rds://db-instance` resource
2. Get detailed instance info with `aws-rds://db-instance/{instance_id}`
3. Check recent events with `DescribeRDSEvents`
4. Review recommendations with `DescribeRDSRecommendations`

## Development

### Running Tests
```bash
uv venv
source .venv/bin/activate
uv sync
uv run --frozen pytest
```

### Building Docker Image
```bash
docker build -t awslabs/rds-monitoring-mcp-server .
```

### Running Docker Container
```bash
docker run -p 8888:8888 \
  -e AWS_PROFILE=default \
  -e AWS_REGION=us-west-2 \
  awslabs/rds-monitoring-mcp-server
```

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
