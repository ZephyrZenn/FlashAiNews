-- Migration: Add focus column to excluded_feed_item_ids table
-- This migration adds focus field to enable topic-level exclusion instead of group-level
-- Run this migration to allow articles to be reused across different topics/focuses

-- Step 1: Add focus column (nullable to support existing data and empty focus)
ALTER TABLE excluded_feed_item_ids
ADD COLUMN IF NOT EXISTS focus VARCHAR(512) DEFAULT '';

-- Step 2: Update existing records to have empty focus (backward compatibility)
UPDATE excluded_feed_item_ids
SET focus = ''
WHERE focus IS NULL;

-- Step 3: Make focus NOT NULL with default empty string
ALTER TABLE excluded_feed_item_ids
ALTER COLUMN focus SET NOT NULL,
ALTER COLUMN focus SET DEFAULT '';

-- Step 4: Create index for focus-based queries
CREATE INDEX IF NOT EXISTS idx_excluded_feed_item_ids_focus 
ON excluded_feed_item_ids (focus, pub_date);

-- Step 5: Create composite index for efficient lookups
CREATE INDEX IF NOT EXISTS idx_excluded_feed_item_ids_item_focus 
ON excluded_feed_item_ids (item_id, focus, pub_date);

-- Step 6: Add comment for documentation
COMMENT ON COLUMN excluded_feed_item_ids.focus IS 
'User focus/topic for this exclusion. Empty string means no specific focus. Articles excluded for one focus can be reused for different focuses.';
