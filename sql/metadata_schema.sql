-- Metadata-Driven Rules Engine Framework
-- Database Schema for Aurora PostgreSQL
-- This schema stores all metadata for rules, data sources, assignments, and results

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- DATA SOURCES TABLE
-- Stores connection information for various data sources
-- ============================================================================
CREATE TABLE IF NOT EXISTS data_sources (
    source_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_name VARCHAR(255) NOT NULL UNIQUE,
    source_type VARCHAR(50) NOT NULL CHECK (source_type IN (
        'databricks', 'sqlserver', 'teradata', 's3', 
        'redshift', 'aurora_postgresql', 'mysql', 'oracle'
    )),
    connection_config JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    description TEXT
);

CREATE INDEX idx_data_sources_type ON data_sources(source_type);
CREATE INDEX idx_data_sources_active ON data_sources(is_active);

-- ============================================================================
-- VALIDATION RULES TABLE
-- Stores reusable validation rules
-- ============================================================================
CREATE TABLE IF NOT EXISTS validation_rules (
    rule_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_name VARCHAR(255) NOT NULL,
    rule_type VARCHAR(50) NOT NULL CHECK (rule_type IN (
        'single_field', 'multi_field', 'cross_table'
    )),
    rule_category VARCHAR(50) NOT NULL CHECK (rule_category IN (
        'completeness', 'accuracy', 'consistency', 
        'integrity', 'timeliness', 'custom'
    )),
    severity_level VARCHAR(20) NOT NULL CHECK (severity_level IN (
        'critical', 'high', 'medium', 'low'
    )),
    rule_logic TEXT NOT NULL, -- SQL/Python expression
    threshold_value NUMERIC(10, 4), -- Optional threshold for pass/fail
    is_reusable BOOLEAN DEFAULT TRUE,
    description TEXT,
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(255),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_validation_rules_type ON validation_rules(rule_type);
CREATE INDEX idx_validation_rules_category ON validation_rules(rule_category);
CREATE INDEX idx_validation_rules_severity ON validation_rules(severity_level);
CREATE INDEX idx_validation_rules_active ON validation_rules(is_active);

-- ============================================================================
-- RULE ASSIGNMENTS TABLE
-- Maps rules to specific tables/columns in data sources
-- ============================================================================
CREATE TABLE IF NOT EXISTS rule_assignments (
    assignment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_id UUID NOT NULL REFERENCES validation_rules(rule_id) ON DELETE CASCADE,
    source_id UUID NOT NULL REFERENCES data_sources(source_id) ON DELETE CASCADE,
    schema_name VARCHAR(255) NOT NULL,
    table_name VARCHAR(255) NOT NULL,
    column_names JSONB NOT NULL, -- Array of column names
    execution_frequency VARCHAR(50) NOT NULL CHECK (execution_frequency IN (
        'batch', 'streaming', 'scheduled', 'on_demand'
    )),
    schedule_expression VARCHAR(255), -- Cron expression for scheduled executions
    is_active BOOLEAN DEFAULT TRUE,
    priority_order INTEGER DEFAULT 0,
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(255),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    additional_config JSONB, -- Additional rule-specific configuration
    CONSTRAINT unique_rule_assignment UNIQUE (rule_id, source_id, schema_name, table_name, column_names)
);

CREATE INDEX idx_rule_assignments_rule ON rule_assignments(rule_id);
CREATE INDEX idx_rule_assignments_source ON rule_assignments(source_id);
CREATE INDEX idx_rule_assignments_table ON rule_assignments(source_id, schema_name, table_name);
CREATE INDEX idx_rule_assignments_active ON rule_assignments(is_active);
CREATE INDEX idx_rule_assignments_frequency ON rule_assignments(execution_frequency);

-- ============================================================================
-- VALIDATION RESULTS TABLE
-- Stores results of rule executions
-- ============================================================================
CREATE TABLE IF NOT EXISTS validation_results (
    result_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_id UUID NOT NULL REFERENCES validation_rules(rule_id),
    assignment_id UUID NOT NULL REFERENCES rule_assignments(assignment_id),
    execution_id UUID NOT NULL,
    validation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    records_checked BIGINT NOT NULL DEFAULT 0,
    records_failed BIGINT NOT NULL DEFAULT 0,
    records_passed BIGINT NOT NULL DEFAULT 0,
    failure_rate NUMERIC(10, 4), -- Percentage of failures
    failure_details JSONB, -- Detailed failure information
    status VARCHAR(20) NOT NULL CHECK (status IN ('pass', 'fail', 'error', 'warning')),
    execution_duration_ms INTEGER,
    error_message TEXT,
    sample_failed_records JSONB, -- Sample of failed records for debugging
    metadata JSONB -- Additional metadata about the execution
);

CREATE INDEX idx_validation_results_rule ON validation_results(rule_id);
CREATE INDEX idx_validation_results_assignment ON validation_results(assignment_id);
CREATE INDEX idx_validation_results_execution ON validation_results(execution_id);
CREATE INDEX idx_validation_results_timestamp ON validation_results(validation_timestamp);
CREATE INDEX idx_validation_results_status ON validation_results(status);
CREATE INDEX idx_validation_results_rule_timestamp ON validation_results(rule_id, validation_timestamp DESC);

-- ============================================================================
-- EXECUTION LOGS TABLE
-- Tracks all execution runs for audit and monitoring
-- ============================================================================
CREATE TABLE IF NOT EXISTS execution_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    execution_id UUID NOT NULL UNIQUE,
    execution_type VARCHAR(50) NOT NULL CHECK (execution_type IN (
        'batch', 'streaming', 'scheduled', 'on_demand', 'ad_hoc'
    )),
    source_id UUID REFERENCES data_sources(source_id),
    assignment_id UUID REFERENCES rule_assignments(assignment_id),
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) NOT NULL CHECK (status IN (
        'running', 'completed', 'failed', 'cancelled', 'timeout'
    )),
    error_message TEXT,
    error_stack_trace TEXT,
    records_processed BIGINT DEFAULT 0,
    execution_duration_ms INTEGER,
    metadata JSONB, -- Additional context (trigger source, user, etc.)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_execution_logs_execution_id ON execution_logs(execution_id);
CREATE INDEX idx_execution_logs_type ON execution_logs(execution_type);
CREATE INDEX idx_execution_logs_source ON execution_logs(source_id);
CREATE INDEX idx_execution_logs_status ON execution_logs(status);
CREATE INDEX idx_execution_logs_start_time ON execution_logs(start_time DESC);

-- ============================================================================
-- RULE VERSION HISTORY TABLE
-- Tracks changes to rules for version control
-- ============================================================================
CREATE TABLE IF NOT EXISTS rule_version_history (
    version_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_id UUID NOT NULL REFERENCES validation_rules(rule_id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    rule_name VARCHAR(255) NOT NULL,
    rule_logic TEXT NOT NULL,
    changed_by VARCHAR(255) NOT NULL,
    change_reason TEXT,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_current_version BOOLEAN DEFAULT FALSE,
    CONSTRAINT unique_rule_version UNIQUE (rule_id, version_number)
);

CREATE INDEX idx_rule_version_history_rule ON rule_version_history(rule_id);
CREATE INDEX idx_rule_version_history_current ON rule_version_history(rule_id, is_current_version);

-- ============================================================================
-- DATA LINEAGE TABLE
-- Tracks data lineage and rule application history
-- ============================================================================
CREATE TABLE IF NOT EXISTS data_lineage (
    lineage_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    execution_id UUID NOT NULL REFERENCES execution_logs(execution_id),
    source_id UUID NOT NULL REFERENCES data_sources(source_id),
    schema_name VARCHAR(255) NOT NULL,
    table_name VARCHAR(255) NOT NULL,
    data_version VARCHAR(255), -- Data version/snapshot identifier
    rules_applied JSONB, -- Array of rule IDs applied
    snapshot_location VARCHAR(500), -- S3 path or location of data snapshot
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_data_lineage_execution ON data_lineage(execution_id);
CREATE INDEX idx_data_lineage_source ON data_lineage(source_id);
CREATE INDEX idx_data_lineage_table ON data_lineage(source_id, schema_name, table_name);

-- ============================================================================
-- QUALITY SCORES TABLE
-- Stores calculated data quality scores
-- ============================================================================
CREATE TABLE IF NOT EXISTS quality_scores (
    score_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID REFERENCES data_sources(source_id),
    schema_name VARCHAR(255),
    table_name VARCHAR(255),
    score_date DATE NOT NULL,
    overall_score NUMERIC(5, 2) NOT NULL CHECK (overall_score >= 0 AND overall_score <= 100),
    completeness_score NUMERIC(5, 2),
    accuracy_score NUMERIC(5, 2),
    consistency_score NUMERIC(5, 2),
    integrity_score NUMERIC(5, 2),
    timeliness_score NUMERIC(5, 2),
    total_rules_applied INTEGER DEFAULT 0,
    rules_passed INTEGER DEFAULT 0,
    rules_failed INTEGER DEFAULT 0,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_quality_score UNIQUE (source_id, schema_name, table_name, score_date)
);

CREATE INDEX idx_quality_scores_source ON quality_scores(source_id);
CREATE INDEX idx_quality_scores_table ON quality_scores(source_id, schema_name, table_name);
CREATE INDEX idx_quality_scores_date ON quality_scores(score_date DESC);

-- ============================================================================
-- TRIGGERS FOR UPDATED_AT TIMESTAMPS
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_data_sources_updated_at BEFORE UPDATE ON data_sources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_validation_rules_updated_at BEFORE UPDATE ON validation_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_rule_assignments_updated_at BEFORE UPDATE ON rule_assignments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View: Recent validation results summary
CREATE OR REPLACE VIEW v_recent_validation_summary AS
SELECT 
    vr.rule_id,
    vr.rule_name,
    vr.rule_category,
    vr.severity_level,
    ds.source_name,
    ra.schema_name,
    ra.table_name,
    vres.validation_timestamp,
    vres.records_checked,
    vres.records_failed,
    vres.status,
    vres.execution_duration_ms
FROM validation_results vres
JOIN validation_rules vr ON vres.rule_id = vr.rule_id
JOIN rule_assignments ra ON vres.assignment_id = ra.assignment_id
JOIN data_sources ds ON ra.source_id = ds.source_id
ORDER BY vres.validation_timestamp DESC;

-- View: Rule execution statistics
CREATE OR REPLACE VIEW v_rule_execution_stats AS
SELECT 
    vr.rule_id,
    vr.rule_name,
    COUNT(vres.result_id) as total_executions,
    SUM(CASE WHEN vres.status = 'pass' THEN 1 ELSE 0 END) as pass_count,
    SUM(CASE WHEN vres.status = 'fail' THEN 1 ELSE 0 END) as fail_count,
    SUM(CASE WHEN vres.status = 'error' THEN 1 ELSE 0 END) as error_count,
    AVG(vres.execution_duration_ms) as avg_duration_ms,
    MAX(vres.validation_timestamp) as last_execution
FROM validation_rules vr
LEFT JOIN validation_results vres ON vr.rule_id = vres.rule_id
GROUP BY vr.rule_id, vr.rule_name;

-- ============================================================================
-- INITIAL DATA (Optional seed data)
-- ============================================================================

-- Insert a sample data source (can be removed in production)
-- INSERT INTO data_sources (source_name, source_type, connection_config, created_by)
-- VALUES (
--     'Sample S3 Source',
--     's3',
--     '{"bucket": "my-data-bucket", "region": "us-east-1"}'::jsonb,
--     'system'
-- );

COMMENT ON TABLE data_sources IS 'Stores connection information for various data sources';
COMMENT ON TABLE validation_rules IS 'Stores reusable validation rules';
COMMENT ON TABLE rule_assignments IS 'Maps rules to specific tables/columns in data sources';
COMMENT ON TABLE validation_results IS 'Stores results of rule executions';
COMMENT ON TABLE execution_logs IS 'Tracks all execution runs for audit and monitoring';
COMMENT ON TABLE rule_version_history IS 'Tracks changes to rules for version control';
COMMENT ON TABLE data_lineage IS 'Tracks data lineage and rule application history';
COMMENT ON TABLE quality_scores IS 'Stores calculated data quality scores';
