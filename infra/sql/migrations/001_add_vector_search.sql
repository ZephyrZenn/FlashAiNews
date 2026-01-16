-- Migration: Add vector search support to summary_memories table
-- This migration adds pgvector extension and embedding column for semantic search
-- Run this migration to enable vector similarity search on historical memories

-- Step 1: Enable pgvector extension
-- Note: This requires pgvector to be installed on your PostgreSQL server
-- For Docker: use pgvector/pgvector image or install the extension
-- For managed services: check if pgvector is available (e.g., Supabase, Neon)
CREATE EXTENSION IF NOT EXISTS vector;

-- Step 2: Add embedding column to summary_memories table
-- Using 1536 dimensions (text-embedding-3-small default)
-- Change to 3072 for text-embedding-3-large if needed
ALTER TABLE summary_memories
ADD COLUMN IF NOT EXISTS embedding vector(1536);

-- Step 3: Create index for vector similarity search
-- Using HNSW index for better performance on approximate nearest neighbor search
-- ef_construction=128 and m=16 are reasonable defaults for most use cases
CREATE INDEX IF NOT EXISTS idx_summary_memories_embedding 
ON summary_memories 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 128);

-- Step 4: Add a comment for documentation
COMMENT ON COLUMN summary_memories.embedding IS 
'Vector embedding (1536 dim) for semantic search. Generated using OpenAI text-embedding-3-small.';

-- Verification query (optional, run manually to verify):
-- SELECT COUNT(*) FROM summary_memories WHERE embedding IS NULL;
