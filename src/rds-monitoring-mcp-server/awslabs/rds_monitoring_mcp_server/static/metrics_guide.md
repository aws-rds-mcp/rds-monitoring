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

# Amazon RDS Metrics Guide

This document outlines available metrics for Amazon RDS database monitoring and provides links to relevant AWS documentation.

## CloudWatch Metrics

### RDS Instance Metrics
- [CPU Utilization](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/MonitoringOverview.html#metrics-reference) - The percentage of CPU utilization.
- [Database Connections](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/MonitoringOverview.html#metrics-reference) - The number of client connections to the DB instance.
- [Freeable Memory](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/MonitoringOverview.html#metrics-reference) - The amount of available random access memory.
- [Read IOPS](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/MonitoringOverview.html#metrics-reference) - The average number of disk I/O read operations per second.
- [Write IOPS](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/MonitoringOverview.html#metrics-reference) - The average number of disk I/O write operations per second.
- [Disk Queue Depth](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/MonitoringOverview.html#metrics-reference) - The number of outstanding IOs (read/write requests) waiting to access the disk.
- [Free Storage Space](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/MonitoringOverview.html#metrics-reference) - The amount of available storage space.

### Aurora Specific Metrics
- [ServerlessDatabaseCapacity](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Aurora.AuroraServerless.html#aurora-serverless-monitoring) - The current capacity of an Aurora Serverless DB cluster.
- [ACUUtilization](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Aurora.AuroraServerless.html#aurora-serverless-monitoring) - The percentage of Aurora capacity units (ACUs) in use.
- [BufferCacheHitRatio](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Aurora.Monitoring.html) - The percentage of requests that are served by the buffer cache.
- [VolumeBytesUsed](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Aurora.Monitoring.html) - The amount of storage used by your Aurora DB cluster.
- [AuroraReplicaLag](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Aurora.Monitoring.html) - For an Aurora Replica, the amount of lag when replicating updates from the primary instance.

### Global Database Metrics
- [GlobalDatabaseReplicatedIORate](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-global-database-monitoring.html) - I/O operations replicated from the primary AWS Region to a secondary AWS Region per second.
- [GlobalDatabaseDataTransferBytes](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-global-database-monitoring.html) - The number of bytes of redo log data transferred from the primary AWS Region to a secondary AWS Region.
- [GlobalDatabaseReplicationLag](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-global-database-monitoring.html) - The lag when replicating updates from the primary AWS Region to a secondary AWS Region, in milliseconds.

### Multi-AZ Cluster Metrics
- [ReplicaLag](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.RDS_Fea_Regions_DB-eng.Feature.MultiAZ_DB_Clusters.html#Concepts.MultiAZ_DB_Clusters.Monitoring) - The amount of time a replica DB instance lags behind the primary DB instance.
- [OldestReplicationSlotLag](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.RDS_Fea_Regions_DB-eng.Feature.MultiAZ_DB_Clusters.html#Concepts.MultiAZ_DB_Clusters.Monitoring) - The lagging size of the replication slot that is most behind.
- [TransactionLogsDiskUsage](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.RDS_Fea_Regions_DB-eng.Feature.MultiAZ_DB_Clusters.html#Concepts.MultiAZ_DB_Clusters.Monitoring) - The amount of disk space used by transaction logs.

### Comprehensive Metric Lists
- [CloudWatch Metrics for Amazon RDS](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/rds-metrics.html) - Complete list of RDS metrics available via CloudWatch.
- [Aurora MySQL CloudWatch Metrics](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Aurora.AuroraMySQL.Monitoring.Metrics.html) - Aurora MySQL specific metrics.
- [Aurora PostgreSQL CloudWatch Metrics](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Aurora.AuroraPostgreSQL.Monitoring.Metrics.html) - Aurora PostgreSQL specific metrics.

## Performance Insights Metrics

### Counter Metrics
- [db.SQL.tpm](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PerfInsights.UsingDashboard.Components.AnalyzeDBLoad.AdditionalMetrics.html) - Transactions per minute.
- [db.SQL.calls](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PerfInsights.UsingDashboard.Components.AnalyzeDBLoad.AdditionalMetrics.html) - SQL calls per second.
- [db.SQL.errors](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PerfInsights.UsingDashboard.Components.AnalyzeDBLoad.AdditionalMetrics.html) - SQL errors per second.
- [db.SQL.latency](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PerfInsights.UsingDashboard.Components.AnalyzeDBLoad.AdditionalMetrics.html) - Average latency of SQL statements in milliseconds.
- [db.SQL.rows](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PerfInsights.UsingDashboard.Components.AnalyzeDBLoad.AdditionalMetrics.html) - Rows processed per SQL call.

### Database Load Metrics
- [db.load.avg](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PerfInsights.UsingDashboard.Metrics.html) - The average active sessions in the database engine.
- [db.load.max](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PerfInsights.UsingDashboard.Metrics.html) - The maximum active sessions in the database engine.

### Dimensions for Load Analysis
- [db.sql](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PerfInsights.UsingDashboard.AnalyzeDBLoad.AdditionalMetrics.html) - SQL statements that are currently running.
- [db.sql_tokenized](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PerfInsights.UsingDashboard.AnalyzeDBLoad.AdditionalMetrics.html) - All SQL statements with literals removed.
- [db.wait_event](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PerfInsights.UsingDashboard.AnalyzeDBLoad.AdditionalMetrics.html) - Shows where the database engine is waiting for resources.
- [db.host](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PerfInsights.UsingDashboard.AnalyzeDBLoad.AdditionalMetrics.html) - Client host connected to the database.
- [db.user](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PerfInsights.UsingDashboard.AnalyzeDBLoad.AdditionalMetrics.html) - Database user logged in to the database.

### Performance Insights Documentation
- [Overview of Performance Insights](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PerfInsights.html) - Introduction to Performance Insights.
- [Performance Insights Dashboard](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PerfInsights.UsingDashboard.html) - Using the dashboard to monitor database load.
- [Database Load Chart](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PerfInsights.UsingDashboard.Components.DBLoad.html) - Understanding the DB load chart.
- [Top Load Items](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PerfInsights.UsingDashboard.Components.TopLoadItems.html) - Analyzing top contributors to database load.

## Wait Events

### MySQL/Aurora MySQL Wait Events
- [CPU Wait Events](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraMySQL.Reference.html#AuroraMySQL.Reference.Waitevents.CPU) - Events related to CPU resource usage.
- [IO Wait Events](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraMySQL.Reference.html#AuroraMySQL.Reference.Waitevents.IO) - Events related to disk and network I/O operations.
- [Lock Wait Events](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraMySQL.Reference.html#AuroraMySQL.Reference.Waitevents.Lock) - Events related to database locks.
- [Buffer Wait Events](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraMySQL.Reference.html#AuroraMySQL.Reference.Waitevents.Buffer) - Events related to buffer pool.

### PostgreSQL/Aurora PostgreSQL Wait Events
- [CPU Wait Events](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraPostgreSQL.Reference.html#AuroraPostgreSQL.Reference.Waitevents.CPU) - Events related to CPU resource usage.
- [IO Wait Events](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraPostgreSQL.Reference.html#AuroraPostgreSQL.Reference.Waitevents.IO) - Events related to disk and network I/O operations.
- [Lock Wait Events](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraPostgreSQL.Reference.html#AuroraPostgreSQL.Reference.Waitevents.Lock) - Events related to database locks.
- [LWLock Wait Events](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraPostgreSQL.Reference.html#AuroraPostgreSQL.Reference.Waitevents.LWLock) - Events related to lightweight locks.
- [Timeout Wait Events](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraPostgreSQL.Reference.html#AuroraPostgreSQL.Reference.Waitevents.Timeout) - Events related to timeouts.

### Wait Event Analysis
- [Using Performance Insights Dashboard](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PerfInsights.UsingDashboard.html#USER_PerfInsights.UsingDashboard.AnalyzeDBLoad) - How to analyze database load by wait events.
- [Tuning with Wait Events](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PerfInsights.UsingDashboard.Components.AnalyzeDBLoad.html) - How to use wait events for performance tuning.

## Enhanced Monitoring

### Operating System Metrics
- [OS Process List](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_Monitoring.OS.html#USER_Monitoring.OS.CloudWatchLogs) - List of processes running on the DB instance.
- [CPU Metrics](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_Monitoring.OS.html#USER_Monitoring.OS.CloudWatchLogs.CPUUtilization) - Detailed CPU utilization metrics.
- [Memory Metrics](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_Monitoring.OS.html#USER_Monitoring.OS.CloudWatchLogs.Memory) - Physical and swap memory usage.
- [IO Metrics](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_Monitoring.OS.html#USER_Monitoring.OS.CloudWatchLogs.DiskIO) - Read and write operations to storage devices.
- [Network Metrics](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_Monitoring.OS.html#USER_Monitoring.OS.CloudWatchLogs.Network) - Network traffic to and from the DB instance.
- [File System Metrics](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_Monitoring.OS.html#USER_Monitoring.OS.CloudWatchLogs.FileSystem) - Disk space usage by file system.

### Enhanced Monitoring Documentation
- [Overview of Enhanced Monitoring](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_Monitoring.OS.html) - Introduction to Enhanced Monitoring.
- [Setting Up Enhanced Monitoring](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_Monitoring.OS.Enabling.html) - How to enable and configure Enhanced Monitoring.
- [Viewing Enhanced Monitoring](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_Monitoring.OS.Viewing.html) - How to access Enhanced Monitoring metrics.

## Database Logs

### Log Types
- [MySQL Error Log](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_LogAccess.Concepts.MySQL.html#USER_LogAccess.MySQL.ErrorLog) - Information about errors, startups, and shutdowns.
- [MySQL General Query Log](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_LogAccess.Concepts.MySQL.html#USER_LogAccess.MySQL.GeneralLog) - Record of client connections and SQL statements.
- [MySQL Slow Query Log](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_LogAccess.Concepts.MySQL.html#USER_LogAccess.MySQL.SlowQuery) - SQL statements that took longer than long_query_time to execute.
- [PostgreSQL Error Log](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_LogAccess.Concepts.PostgreSQL.html) - Record of database errors and startup messages.
- [PostgreSQL Log](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_LogAccess.Concepts.PostgreSQL.html) - Contains connection, DDL, and error information.
- [Aurora PostgreSQL Log](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/USER_LogAccess.Concepts.PostgreSQL.html) - Aurora PostgreSQL specific logging.

### Log Access Documentation
- [Overview of RDS Log Files](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_LogAccess.html) - Introduction to database logs.
- [Monitoring Log Files](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_Monitoring.html#CHAP_Monitoring.Logs) - How to monitor database log files.
- [Publishing Logs to CloudWatch](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_LogAccess.Procedural.UploadtoCloudWatch.html) - How to publish RDS logs to CloudWatch Logs.

## Events and Notifications

### RDS Events
- [DB Instance Events](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_Events.html#USER_Events.Messages.instance) - Events related to database instances.
- [DB Cluster Events](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_Events.html#USER_Events.Messages.cluster) - Events related to database clusters.
- [DB Parameter Group Events](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_Events.html#USER_Events.Messages.parameter-group) - Events related to parameter groups.
- [DB Security Group Events](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_Events.html#USER_Events.Messages.security-group) - Events related to security groups.
- [DB Snapshot Events](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_Events.html#USER_Events.Messages.snapshot) - Events related to database snapshots.

### Event Documentation
- [Working with RDS Events](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_Events.html) - Overview of RDS events.
- [Creating RDS Event Notifications](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_Events.html) - How to set up event notifications.
- [Viewing RDS Events](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_ListEvents.html) - How to view RDS events.

## Recommendations and Advisors

### Performance Insights Analytics
- [Performance Analysis](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PerfInsights.Analytics.html) - How to analyze database performance issues.
- [Performance Anomaly Detection](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PerfInsights.UsingDashboard.Components.AnalysisPanel.html) - Identifying anomalous performance patterns.
- [Performance Database Insight](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_RDSDevOps.Overview.html) - Tools for diagnosing and resolving performance issues.

### RDS Recommendations
- [DevOps Guru for RDS](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/devops-guru-for-rds.html) - Proactive performance recommendations.
- [Trusted Advisor Recommendations](https://docs.aws.amazon.com/awssupport/latest/user/trusted-advisor-check-reference.html#amazon-rds-checks) - Best practice recommendations for RDS.

## Integration with Other AWS Services

### CloudWatch Integration
- [CloudWatch Metrics for RDS](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/rds-metricscollected.html) - How RDS metrics are published to CloudWatch.
- [CloudWatch Alarms for RDS](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_Events.html#USER_Events.overview) - Setting up alarms for RDS metrics.
- [CloudWatch Logs for RDS](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_LogAccess.Procedural.UploadtoCloudWatch.html) - Publishing RDS logs to CloudWatch Logs.

### EventBridge Integration
- [EventBridge for RDS Events](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/rds-cloudwatch-events.html) - How to use EventBridge with RDS events.
- [Automating RDS with EventBridge](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/rds-cloudwatch-events.html#rds-cloudwatch-events-integrating) - Automating responses to RDS events.

## Best Practices

### Monitoring Best Practices
- [RDS Monitoring Best Practices](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_BestPractices.html#CHAP_BestPractices.Performance) - General best practices for monitoring RDS.
- [Performance Insights Best Practices](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PerfInsights.BestPractices.html) - How to effectively use Performance Insights.
- [Enhanced Monitoring Best Practices](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_Monitoring.OS.html#USER_Monitoring.OS.bestpractices) - Best practices for using Enhanced Monitoring.

### Database Engine Specific Monitoring
- [Aurora MySQL Monitoring](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraMySQL.Monitoring.html) - Aurora MySQL specific monitoring guidance.
- [Aurora PostgreSQL Monitoring](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraPostgreSQL.Monitoring.html) - Aurora PostgreSQL specific monitoring guidance.
- [RDS MySQL Monitoring](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/MySQL.Monitoring.html) - RDS MySQL specific monitoring guidance.
- [RDS PostgreSQL Monitoring](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/PostgreSQL.Monitoring.html) - RDS PostgreSQL specific monitoring guidance.
