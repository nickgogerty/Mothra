-- Initialize PostgreSQL database for MOTHRA
-- This script runs automatically when Docker container starts

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create custom types for better type safety
DO $$ BEGIN
    CREATE TYPE entity_type AS ENUM ('process', 'material', 'product', 'service', 'energy');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE validation_status AS ENUM ('pending', 'validated', 'rejected');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE crawl_status AS ENUM ('running', 'completed', 'failed', 'partial');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE mothra TO mothra;
GRANT ALL PRIVILEGES ON SCHEMA public TO mothra;

-- Performance tuning for pgvector
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '128MB';
ALTER SYSTEM SET max_wal_size = '2GB';

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'MOTHRA database initialized successfully';
END $$;
