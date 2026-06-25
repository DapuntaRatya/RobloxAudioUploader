PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS api_sessions (
    session_id TEXT PRIMARY KEY,
    authorized_user_id TEXT NOT NULL,
    api_key_name TEXT NOT NULL,
    api_key_encrypted TEXT NOT NULL,
    api_key_masked TEXT NOT NULL,
    scopes_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TEXT NOT NULL,
    revoked_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_api_sessions_expires_at
ON api_sessions(expires_at);

CREATE TABLE IF NOT EXISTS upload_jobs (
    job_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    authorized_user_id TEXT NOT NULL,
    source_type TEXT NOT NULL,
    status TEXT NOT NULL,
    total_items INTEGER NOT NULL DEFAULT 0,
    total_success INTEGER NOT NULL DEFAULT 0,
    total_failed INTEGER NOT NULL DEFAULT 0,
    experience_ids_json TEXT NOT NULL DEFAULT '[]',
    options_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TEXT,
    finished_at TEXT,
    cancelled_at TEXT,
    FOREIGN KEY(session_id) REFERENCES api_sessions(session_id)
);

CREATE INDEX IF NOT EXISTS idx_upload_jobs_session_id
ON upload_jobs(session_id);

CREATE INDEX IF NOT EXISTS idx_upload_jobs_status
ON upload_jobs(status);

CREATE TABLE IF NOT EXISTS upload_items (
    item_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    item_index INTEGER NOT NULL,
    source_url TEXT NOT NULL,
    status TEXT NOT NULL,
    download_title TEXT,
    temp_file_path TEXT,
    asset_id TEXT,
    error_message TEXT,
    error_details_json TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TEXT,
    finished_at TEXT,
    FOREIGN KEY(job_id) REFERENCES upload_jobs(job_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_upload_items_job_id
ON upload_items(job_id);

CREATE TABLE IF NOT EXISTS upload_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    item_id TEXT,
    event_type TEXT NOT NULL,
    level TEXT NOT NULL,
    message TEXT NOT NULL,
    data_json TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(job_id) REFERENCES upload_jobs(job_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_upload_events_job_id_id
ON upload_events(job_id, id);
