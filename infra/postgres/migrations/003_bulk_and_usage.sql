-- Phase 3: Bulk Processing and Metering

CREATE TABLE IF NOT EXISTS bulk_jobs (
    job_id VARCHAR(50) PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'queued',
    total_rows INTEGER NOT NULL DEFAULT 0,
    processed_rows INTEGER NOT NULL DEFAULT 0,
    failed_rows INTEGER NOT NULL DEFAULT 0,
    summary_json JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE decisions ADD COLUMN IF NOT EXISTS bulk_job_id VARCHAR(50);
ALTER TABLE returns ADD COLUMN IF NOT EXISTS bulk_job_id VARCHAR(50);

CREATE TABLE IF NOT EXISTS usage_events (
    event_id VARCHAR(50) PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,
    event_type VARCHAR(50) NOT NULL, -- 'return_processed', 'bulk_row', 'api_call', 'llm_tokens'
    api_call VARCHAR(100),
    llm_tokens INTEGER DEFAULT 0,
    store_id VARCHAR(50),
    quantity INTEGER DEFAULT 1,
    ts TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_bulk_jobs_tenant ON bulk_jobs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_usage_events_tenant ON usage_events(tenant_id, ts);
