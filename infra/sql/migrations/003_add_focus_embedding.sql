-- Migration: Add focus_embedding column to excluded_feed_item_ids table
-- This migration adds vector embedding support for semantic focus matching
-- Run this migration to enable semantic similarity matching for focus (e.g., "AI安全" ≈ "人工智能安全")

-- Step 1: Ensure pgvector extension is enabled (should already be done in 001_add_vector_search.sql)
CREATE EXTENSION IF NOT EXISTS vector;

-- Step 2: Add focus_embedding column (nullable, only populated if embedding service is configured)
-- Using 1536 dimensions (text-embedding-3-small default)
-- Change to 3072 for text-embedding-3-large if needed
ALTER TABLE excluded_feed_item_ids
ADD COLUMN IF NOT EXISTS focus_embedding vector(1536);

-- Step 3: Create index for vector similarity search on focus_embedding
-- Using HNSW index for better performance on approximate nearest neighbor search
CREATE INDEX IF NOT EXISTS idx_excluded_feed_item_ids_focus_embedding 
ON excluded_feed_item_ids 
USING hnsw (focus_embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 128)
WHERE focus_embedding IS NOT NULL;  -- Partial index, only index non-null embeddings

-- Step 4: Add comment for documentation
COMMENT ON COLUMN excluded_feed_item_ids.focus_embedding IS 
'Vector embedding (1536 dim) for semantic focus matching. Generated using OpenAI text-embedding-3-small. 
Allows "AI安全" and "人工智能安全" to be treated as the same focus. NULL if embedding service not configured.';
