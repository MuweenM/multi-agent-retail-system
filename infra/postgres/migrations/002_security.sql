-- Migration 002_security.sql
-- Adds password_hash column to users table and inserts demo users.

ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash TEXT;

-- Password for all demo users is "password"
-- bcrypt hash for "password": $2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjIQqiRQYq

INSERT INTO users (user_id, tenant_id, email, role, password_hash)
VALUES 
    ('u_admin', 'demo', 'admin@demo.com', 'admin', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjIQqiRQYq'),
    ('u_reviewer', 'demo', 'reviewer@demo.com', 'reviewer', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjIQqiRQYq'),
    ('u_viewer', 'demo', 'viewer@demo.com', 'viewer', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjIQqiRQYq')
ON CONFLICT (user_id) DO UPDATE SET password_hash = EXCLUDED.password_hash, role = EXCLUDED.role;
