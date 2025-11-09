-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    hashed_password VARCHAR(255),
    user_type VARCHAR(10) DEFAULT 'registered' CHECK (user_type IN ('guest', 'registered')),
    guest_uuid UUID UNIQUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT registered_user_check CHECK (
        (user_type = 'registered' AND email IS NOT NULL AND hashed_password IS NOT NULL AND guest_uuid IS NULL) OR
        (user_type = 'guest' AND guest_uuid IS NOT NULL)
    )
);

-- URLs table
CREATE TABLE IF NOT EXISTS urls (
    id SERIAL PRIMARY KEY,
    short_code VARCHAR(20) UNIQUE NOT NULL,
    original_url TEXT NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    clicks INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    is_private BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_short_code 
ON urls(short_code) WHERE is_active = TRUE;

-- Index for guest UUID lookups
CREATE INDEX IF NOT EXISTS idx_guest_uuid 
ON users(guest_uuid) WHERE user_type = 'guest';

-- Index for cleanup of expired URLs
CREATE INDEX IF NOT EXISTS idx_urls_expires_at 
ON urls(expires_at) WHERE expires_at IS NOT NULL AND is_active = TRUE;

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
