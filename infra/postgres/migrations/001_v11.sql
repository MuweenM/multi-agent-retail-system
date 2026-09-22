-- Migration 001_v11.sql
-- Adds catalogue tables, updated returns schema, operational tables, and multi-tenant indexes.

-- 1. Catalogue Tables (Shared reference data, no tenant_id)
CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id VARCHAR(50) PRIMARY KEY,
    name TEXT NOT NULL,
    country TEXT NOT NULL,
    quality_tier VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Backward compatibility in case legacy suppliers table existed without supplier_id
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'suppliers') THEN
        ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS supplier_id VARCHAR(50);
        ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS country TEXT;
        ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS quality_tier VARCHAR(20);
        ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(50) PRIMARY KEY,
    name TEXT NOT NULL,
    brand TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,
    price_lkr NUMERIC(12, 2) NOT NULL,
    supplier_id VARCHAR(50),
    return_window_days INT NOT NULL DEFAULT 14,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS return_policies (
    category VARCHAR(50) PRIMARY KEY,
    window_days INT NOT NULL,
    non_returnable_unless_defective BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Multi-tenant Platform Tables
CREATE TABLE IF NOT EXISTS tenants (
    tenant_id VARCHAR(50) PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default demo tenant
INSERT INTO tenants (tenant_id, name)
VALUES ('demo', 'Demo Tenant')
ON CONFLICT (tenant_id) DO NOTHING;

CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(50) PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'agent',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Ingestion & Job Tracking
CREATE TABLE IF NOT EXISTS bulk_jobs (
    job_id VARCHAR(100) PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'queued',
    total INT NOT NULL DEFAULT 0,
    processed INT NOT NULL DEFAULT 0,
    failed INT NOT NULL DEFAULT 0,
    errors JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Returns Core Table
CREATE TABLE IF NOT EXISTS returns (
    return_id VARCHAR(100) PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL DEFAULT 'demo',
    job_id VARCHAR(100),
    product_id VARCHAR(50),
    supplier_id VARCHAR(50),
    batch_id VARCHAR(50),
    courier VARCHAR(50),
    store_id VARCHAR(50),
    customer_ref_hash VARCHAR(128),
    raw_text_enc TEXT,
    clean_text TEXT,
    issue TEXT,
    root_cause_pred VARCHAR(100),
    root_cause_gold VARCHAR(100),
    order_value_lkr NUMERIC(12, 2),
    purchase_date DATE,
    return_date DATE,
    district VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add any missing columns if returns already existed from legacy init.sql
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'returns') THEN
        ALTER TABLE returns ADD COLUMN IF NOT EXISTS return_id VARCHAR(100);
        ALTER TABLE returns ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(50) DEFAULT 'demo';
        ALTER TABLE returns ADD COLUMN IF NOT EXISTS job_id VARCHAR(100);
        ALTER TABLE returns ADD COLUMN IF NOT EXISTS product_id VARCHAR(50);
        ALTER TABLE returns ADD COLUMN IF NOT EXISTS supplier_id VARCHAR(50);
        ALTER TABLE returns ADD COLUMN IF NOT EXISTS batch_id VARCHAR(50);
        ALTER TABLE returns ADD COLUMN IF NOT EXISTS courier VARCHAR(50);
        ALTER TABLE returns ADD COLUMN IF NOT EXISTS store_id VARCHAR(50);
        ALTER TABLE returns ADD COLUMN IF NOT EXISTS customer_ref_hash VARCHAR(128);
        ALTER TABLE returns ADD COLUMN IF NOT EXISTS raw_text_enc TEXT;
        ALTER TABLE returns ADD COLUMN IF NOT EXISTS clean_text TEXT;
        ALTER TABLE returns ADD COLUMN IF NOT EXISTS issue TEXT;
        ALTER TABLE returns ADD COLUMN IF NOT EXISTS root_cause_pred VARCHAR(100);
        ALTER TABLE returns ADD COLUMN IF NOT EXISTS root_cause_gold VARCHAR(100);
        ALTER TABLE returns ADD COLUMN IF NOT EXISTS order_value_lkr NUMERIC(12, 2);
        ALTER TABLE returns ADD COLUMN IF NOT EXISTS purchase_date DATE;
        ALTER TABLE returns ADD COLUMN IF NOT EXISTS return_date DATE;
        ALTER TABLE returns ADD COLUMN IF NOT EXISTS district VARCHAR(100);
        ALTER TABLE returns ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
    END IF;
END $$;

-- 5. Decisions Table
CREATE TABLE IF NOT EXISTS decisions (
    decision_id VARCHAR(100) PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL DEFAULT 'demo',
    return_id VARCHAR(100),
    root_cause VARCHAR(100) NOT NULL,
    confidence FLOAT NOT NULL,
    evidence_summary TEXT,
    recommendation TEXT NOT NULL,
    decision VARCHAR(50) NOT NULL DEFAULT 'escalate',
    requires_human_review BOOLEAN NOT NULL DEFAULT FALSE,
    citations JSONB DEFAULT '[]'::jsonb,
    reasoning_steps JSONB DEFAULT '[]'::jsonb,
    human_review_reasons JSONB DEFAULT '[]'::jsonb,
    risk_flags JSONB DEFAULT '[]'::jsonb,
    agent_trace JSONB DEFAULT '[]'::jsonb,
    evidence_support FLOAT DEFAULT 0.0,
    disclaimer TEXT DEFAULT 'AI suggestion. A person must confirm before any action.',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. Audit & Observability
CREATE TABLE IF NOT EXISTS audit_log (
    audit_id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL DEFAULT 'demo',
    user_id VARCHAR(50),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id VARCHAR(100),
    details JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS usage_events (
    event_id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL DEFAULT 'demo',
    agent VARCHAR(50) NOT NULL,
    tool VARCHAR(100) NOT NULL,
    latency_ms INT NOT NULL DEFAULT 0,
    ok BOOLEAN NOT NULL DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. Multi-tenant Performance Indexes
CREATE INDEX IF NOT EXISTS idx_returns_tenant_product_date
ON returns (tenant_id, product_id, return_date);

CREATE INDEX IF NOT EXISTS idx_decisions_tenant_return
ON decisions (tenant_id, return_id);

CREATE INDEX IF NOT EXISTS idx_bulk_jobs_tenant
ON bulk_jobs (tenant_id, created_at DESC);
