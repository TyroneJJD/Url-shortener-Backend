-- Migration: Add URL Access History table
-- Date: 2025-11-08
-- Description: Creates table to track who accessed private URLs

-- URL Access History table (for tracking who accessed private URLs)
CREATE TABLE IF NOT EXISTS url_access_history (
    id SERIAL PRIMARY KEY,
    url_id INTEGER REFERENCES urls(id) ON DELETE CASCADE,
    user_email VARCHAR(100),
    user_type VARCHAR(10),
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast lookups by URL
CREATE INDEX IF NOT EXISTS idx_url_access_history_url_id 
ON url_access_history(url_id);

-- Add comment to table
COMMENT ON TABLE url_access_history IS 'Tracks access history for private URLs';
COMMENT ON COLUMN url_access_history.url_id IS 'Reference to the URL that was accessed';
COMMENT ON COLUMN url_access_history.user_email IS 'Email of the user who accessed the URL';
COMMENT ON COLUMN url_access_history.user_type IS 'Type of user: guest or registered';
COMMENT ON COLUMN url_access_history.accessed_at IS 'Timestamp when the URL was accessed';
