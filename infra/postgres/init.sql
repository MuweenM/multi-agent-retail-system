-- TODO: adjust columns to match what your agents actually produce.
-- This creates tables automatically the first time Postgres starts.

CREATE TABLE IF NOT EXISTS returns (
    id SERIAL PRIMARY KEY,
    product TEXT NOT NULL,
    issue TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    intent TEXT,
    sentiment TEXT,
    root_cause TEXT,
    confidence FLOAT,
    recommendation TEXT,
    requires_human_review BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS suppliers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    product TEXT NOT NULL,
    quality_flag TEXT
);

CREATE TABLE IF NOT EXISTS inventory (
    id SERIAL PRIMARY KEY,
    product TEXT NOT NULL,
    batch_id TEXT,
    stock_count INT,
    warehouse TEXT
);
