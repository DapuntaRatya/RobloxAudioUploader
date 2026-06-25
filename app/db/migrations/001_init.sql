CREATE TABLE IF NOT EXISTS api_sessions (
    session_id TEXT PRIMARY KEY,
    authorized_user_id TEXT NOT NULL,
    api_key_name TEXT NOT NULL,
    api_key_encrypted TEXT NOT NULL,
    api_key_masked TEXT NOT NULL,
    scopes JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS idx_api_sessions_expires_at ON api_sessions(expires_at);

CREATE TABLE IF NOT EXISTS upload_jobs (
    job_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES api_sessions(session_id),
    authorized_user_id TEXT NOT NULL,
    source_type TEXT NOT NULL,
    status TEXT NOT NULL,
    total_items INT NOT NULL DEFAULT 0,
    total_success INT NOT NULL DEFAULT 0,
    total_failed INT NOT NULL DEFAULT 0,
    experience_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    options JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ NULL,
    finished_at TIMESTAMPTZ NULL,
    cancelled_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS idx_upload_jobs_session_id ON upload_jobs(session_id);
CREATE INDEX IF NOT EXISTS idx_upload_jobs_status ON upload_jobs(status);

CREATE TABLE IF NOT EXISTS upload_items (
    item_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL REFERENCES upload_jobs(job_id) ON DELETE CASCADE,
    item_index INT NOT NULL,
    source_url TEXT NOT NULL,
    status TEXT NOT NULL,
    download_title TEXT NULL,
    temp_file_path TEXT NULL,
    asset_id TEXT NULL,
    error_message TEXT NULL,
    error_details JSONB NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ NULL,
    finished_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS idx_upload_items_job_id ON upload_items(job_id);

CREATE TABLE IF NOT EXISTS upload_events (
    id BIGSERIAL PRIMARY KEY,
    redis_id TEXT NULL,
    job_id TEXT NOT NULL REFERENCES upload_jobs(job_id) ON DELETE CASCADE,
    item_id TEXT NULL,
    event_type TEXT NOT NULL,
    level TEXT NOT NULL,
    message TEXT NOT NULL,
    data JSONB NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_upload_events_job_id_id ON upload_events(job_id, id);
