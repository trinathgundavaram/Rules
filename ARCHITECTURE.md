# Architecture Documentation

## System Overview

The Data Rules Engine Framework is a serverless, metadata-driven data validation platform built on AWS. It provides a centralized way to define, manage, and execute data quality rules across multiple heterogeneous data sources.

## Architecture Principles

1. **Metadata-Driven**: All rules and configurations stored in centralized database
2. **Serverless First**: Leverage AWS Lambda and Glue for automatic scaling
3. **Separation of Concerns**: Clear boundaries between connectors, rules engine, and orchestration
4. **Extensibility**: Plugin architecture for adding new connectors and rule types
5. **Observability**: Comprehensive logging, metrics, and audit trails

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Presentation Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   Web UI     │  │  API Gateway │  │   CloudFront CDN     │  │
│  │   (React)    │  │  (REST API)   │  │   (Static Assets)    │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────────────────┘  │
└─────────┼──────────────────┼─────────────────────────────────────┘
          │                  │
┌─────────▼──────────────────▼─────────────────────────────────────┐
│                      Application Layer                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Lambda Functions                             │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│  │  │ Rule Executor│  │ API Backend  │  │ Notification │  │   │
│  │  │              │  │              │  │   Handler     │  │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │   │
│  └─────────┼──────────────────┼──────────────────┼─────────┘   │
│            │                  │                  │               │
│  ┌─────────▼──────────────────▼──────────────────▼─────────┐   │
│  │              Step Functions (Orchestration)              │   │
│  └───────────────────────────┬───────────────────────────────┘   │
└──────────────────────────────┼────────────────────────────────────┘
                               │
┌──────────────────────────────▼────────────────────────────────────┐
│                      Processing Layer                             │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │              AWS Glue Jobs (PySpark)                     │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │    │
│  │  │Bulk Validator│  │Data Profiler │  │Rule Recommender│ │    │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │    │
│  └─────────┼──────────────────┼──────────────────┼─────────┘    │
│            │                  │                  │                │
│  ┌─────────▼──────────────────▼──────────────────▼─────────┐    │
│  │              Connector Framework                         │    │
│  │  Databricks │ SQL Server │ Teradata │ S3 │ Redshift     │    │
│  └───────────────────────────┬──────────────────────────────┘    │
└──────────────────────────────┼────────────────────────────────────┘
                               │
┌──────────────────────────────▼────────────────────────────────────┐
│                      Data Layer                                   │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │          Metadata Repository (Aurora PostgreSQL)        │    │
│  │  • Rules • Assignments • Results • Sources • Logs       │    │
│  └───────────────────────────┬──────────────────────────────┘    │
│                               │                                    │
│  ┌───────────────────────────▼──────────────────────────────┐    │
│  │              S3 (Results & Code Storage)                 │    │
│  │  • Validation Results • Lambda Packages • UI Assets      │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
                               │
┌──────────────────────────────▼────────────────────────────────────┐
│                    External Data Sources                           │
│  Databricks │ SQL Server │ Teradata │ S3 │ Redshift │ Aurora     │
└──────────────────────────────────────────────────────────────────┘
```

## Component Details

### Presentation Layer

#### Web UI (React)
- **Location**: `src/ui/frontend/`
- **Technology**: React 18+, Material-UI
- **Hosting**: S3 + CloudFront
- **Authentication**: AWS Cognito
- **Features**:
  - Rule library management
  - Rule builder with syntax highlighting
  - Assignment management
  - Results visualization
  - Batch import interface

#### API Gateway
- **Type**: REST API
- **Integration**: Lambda Proxy
- **Authentication**: Cognito User Pool
- **Rate Limiting**: 10,000 requests/second
- **CORS**: Enabled for UI domain

### Application Layer

#### Lambda Functions

**Rule Executor** (`src/lambda/rule_executor/`)
- **Purpose**: Orchestrates validation execution
- **Trigger**: EventBridge schedule, API Gateway
- **Memory**: 512 MB - 3 GB (configurable)
- **Timeout**: 5-15 minutes
- **VPC**: Yes (for database access)
- **Responsibilities**:
  - Fetch active rule assignments
  - Determine execution strategy (Lambda vs Glue)
  - Spawn Glue jobs for large datasets
  - Handle small validations directly
  - Update execution logs

**API Backend** (`src/lambda/api_gateway/`)
- **Purpose**: REST API handler
- **Trigger**: API Gateway
- **Memory**: 256 MB
- **Timeout**: 30 seconds
- **VPC**: Yes (for database access)
- **Responsibilities**:
  - CRUD operations for rules
  - Query validation results
  - Manage data sources
  - Handle batch imports
  - Authentication/authorization

**Notification Handler** (`src/lambda/notification_handler/`)
- **Purpose**: Send alerts on failures
- **Trigger**: SNS topic
- **Memory**: 256 MB
- **Timeout**: 30 seconds
- **VPC**: No
- **Responsibilities**:
  - Format failure messages
  - Send emails/SMS via SNS
  - Integrate with Slack/PagerDuty

#### Step Functions

**Validation Workflow** (`src/step_functions/validation_workflow.json`)
- Orchestrates multi-step validation processes
- Handles retries and error recovery
- Parallel execution of independent validations
- State management for long-running processes

### Processing Layer

#### AWS Glue Jobs

**Bulk Validator** (`src/glue/bulk_validator.py`)
- **Purpose**: Execute validations on large datasets
- **Worker Type**: G.1X, G.2X (configurable)
- **Workers**: 2-50 (configurable)
- **Timeout**: 48 hours
- **Process**:
  1. Read rule assignments from metadata DB
  2. Create appropriate connector
  3. Read source data into Spark DataFrame
  4. Apply validation rules using PySpark
  5. Identify failed records
  6. Write detailed results to S3 (partitioned)
  7. Update metadata DB with summary

**Data Profiler** (`src/glue/data_profiler.py`)
- **Purpose**: Auto-generate rule suggestions
- **Process**:
  - Analyze dataset statistics
  - Detect patterns and anomalies
  - Suggest appropriate validation rules
  - Write recommendations to metadata DB

**Rule Recommender** (`src/glue/rule_recommender.py`)
- **Purpose**: ML-based intelligent rule suggestions
- **Uses**: Historical validation results
- **Output**: Recommended rules for new datasets

#### Connector Framework

**Base Connector** (`src/connectors/base.py`)
- Abstract interface for all connectors
- Defines standard methods: `connect()`, `read_data()`, `write_results()`

**Concrete Implementations**:
- `databricks.py`: Databricks SQL Warehouse
- `sqlserver.py`: SQL Server via ODBC
- `teradata.py`: Teradata via Teradata SQL
- `s3.py`: S3 Parquet/CSV files
- `redshift.py`: Amazon Redshift
- `aurora.py`: Aurora PostgreSQL

**Connector Factory** (`src/connectors/factory.py`)
- Creates appropriate connector based on source type
- Handles connection pooling
- Manages credentials from Secrets Manager

### Data Layer

#### Metadata Repository (Aurora PostgreSQL)

**Database Schema**:
- `data_sources`: Connection configurations
- `validation_rules`: Rule definitions
- `rule_assignments`: Rule-to-table mappings
- `validation_results`: Execution results
- `execution_logs`: Audit trail

**Connection Management**:
- Connection pooling via SQLAlchemy
- Read replicas for query scaling
- Automated backups (7-day retention)
- Multi-AZ deployment for HA

#### S3 Storage

**Buckets**:
- `results-bucket`: Validation results (partitioned by date/rule)
- `code-bucket`: Lambda packages, Glue scripts
- `temp-bucket`: Temporary processing data
- `ui-bucket`: Static web assets

**Partitioning Strategy**:
```
s3://results-bucket/
  validations/
    date=2024-01-15/
      rule_id=abc123/
        results.parquet
        failures.parquet
```

## Data Flow

### Rule Creation Flow

```
1. User creates rule via UI
   ↓
2. API Gateway → Lambda (API Backend)
   ↓
3. Validate rule syntax
   ↓
4. Save to metadata DB (validation_rules table)
   ↓
5. Return success to UI
```

### Validation Execution Flow

```
1. EventBridge triggers scheduled validation
   ↓
2. Lambda (Rule Executor) invoked
   ↓
3. Query metadata DB for active assignments
   ↓
4. For each assignment:
   a. Check dataset size
   b. If large (>10M rows): Spawn Glue job
   c. If small: Execute in Lambda
   ↓
5. Glue Job (if spawned):
   a. Create connector via factory
   b. Read data from source
   c. Apply validation rules
   d. Write results to S3
   e. Update metadata DB
   ↓
6. On failure: Trigger SNS → Notification Handler
   ↓
7. Log execution to execution_logs table
```

### Results Query Flow

```
1. User queries results via UI
   ↓
2. API Gateway → Lambda (API Backend)
   ↓
3. Query metadata DB (validation_results table)
   ↓
4. For detailed results: Read from S3
   ↓
5. Return aggregated data to UI
```

## Security Architecture

### Authentication & Authorization

- **Web UI**: AWS Cognito User Pool
- **API**: Cognito JWT tokens
- **Lambda**: IAM roles with least privilege
- **Database**: Secrets Manager for credentials

### Network Security

- **VPC**: Isolated network for Lambda and RDS
- **Security Groups**: Restrictive ingress/egress rules
- **Private Subnets**: Database in private subnets only
- **NAT Gateway**: Outbound internet access for Lambda

### Data Security

- **Encryption at Rest**: 
  - RDS: AES-256
  - S3: SSE-S3 or SSE-KMS
  - Secrets Manager: KMS encryption
- **Encryption in Transit**: TLS 1.2+ for all connections
- **Secrets Management**: AWS Secrets Manager

### IAM Policies

**Lambda Execution Role**:
- Read from Secrets Manager
- Write to S3 results bucket
- Start Glue jobs
- Publish to SNS
- Query RDS

**Glue Execution Role**:
- Read from Secrets Manager
- Read/write to S3
- Query RDS
- Access data sources (via connector credentials)

## Scalability

### Horizontal Scaling

- **Lambda**: Auto-scales to 1000 concurrent executions
- **Glue**: Scale workers based on data volume
- **RDS**: Read replicas for query scaling
- **API Gateway**: Handles 10,000+ requests/second

### Vertical Scaling

- **Lambda**: Memory up to 10 GB
- **Glue**: Worker types G.1X → G.2X → G.4X
- **RDS**: Instance class upgrades (db.t3 → db.r6g)

### Performance Optimizations

- **Partitioning**: S3 results partitioned by date/rule
- **Caching**: Rule definitions cached in Lambda
- **Parallel Execution**: Multiple validations run concurrently
- **Connection Pooling**: Database connections reused

## Monitoring & Observability

### CloudWatch Metrics

- Lambda invocations, errors, duration
- Glue job runs, failures, DPU hours
- API Gateway requests, latency, 4xx/5xx errors
- RDS CPU, memory, connections, read/write IOPS
- S3 request counts, bytes transferred

### CloudWatch Logs

- All Lambda function logs
- Glue job logs
- Application logs with structured JSON

### CloudWatch Alarms

- Lambda error rate > 5%
- Glue job failure
- API Gateway 5xx errors
- RDS CPU > 80%
- Validation failure rate > threshold

### Dashboards

- Executive dashboard: High-level metrics
- Operational dashboard: Detailed system health
- Business dashboard: Validation pass/fail rates

## Disaster Recovery

### Backup Strategy

- **RDS**: Automated daily snapshots, 7-day retention
- **S3**: Versioning enabled, cross-region replication (optional)
- **Terraform State**: S3 backend with versioning

### Recovery Procedures

1. **Database Restore**: From automated snapshot
2. **Infrastructure Rebuild**: Terraform/Terragrunt
3. **Code Deployment**: From version control
4. **Data Recovery**: S3 versioning or cross-region replica

### RTO/RPO Targets

- **RTO**: 4 hours (infrastructure rebuild)
- **RPO**: 24 hours (daily snapshots)

## Cost Optimization

### Cost Drivers

- **RDS**: Instance hours, storage, backups
- **Lambda**: Invocations, duration, memory
- **Glue**: DPU hours
- **S3**: Storage, requests
- **Data Transfer**: Cross-AZ, internet egress

### Optimization Strategies

- **Reserved Instances**: RDS for production
- **S3 Lifecycle Policies**: Move old results to Glacier
- **Lambda Reserved Concurrency**: Prevent over-scaling
- **Glue Auto Scaling**: Scale down when idle
- **S3 Intelligent Tiering**: Automatic cost optimization

## Extensibility

### Adding New Connectors

1. Implement `BaseConnector` interface
2. Add to `factory.py`
3. Update documentation
4. Add tests

### Adding New Rule Types

1. Extend `RuleExecutor`
2. Implement rule-specific validator
3. Update parser if needed
4. Add to UI rule builder

### Custom Integrations

- **Webhooks**: API Gateway can trigger external systems
- **EventBridge**: Publish custom events
- **SNS Topics**: Subscribe external services

## Future Enhancements

- **Real-time Validation**: Kinesis integration
- **ML-based Anomaly Detection**: SageMaker integration
- **Data Lineage**: Track data flow and dependencies
- **Collaboration Features**: Rule versioning, approvals
- **Advanced Analytics**: Trend analysis, predictive quality metrics
