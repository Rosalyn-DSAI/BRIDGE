CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY, email TEXT NOT NULL UNIQUE,
 auth_scope TEXT NOT NULL, created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS login_tokens (
 digest TEXT PRIMARY KEY, email TEXT NOT NULL, expires_at INTEGER NOT NULL,
 used INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS tasks (
 id TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
 title TEXT NOT NULL, language TEXT NOT NULL, due_at INTEGER NOT NULL,
 timezone TEXT NOT NULL, source_title TEXT NOT NULL, provenance TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'pending', created_at INTEGER NOT NULL,
 details TEXT NOT NULL DEFAULT '{}', completed_at INTEGER
);
CREATE TABLE IF NOT EXISTS reminders (
 id TEXT PRIMARY KEY, task_id TEXT NOT NULL UNIQUE REFERENCES tasks(id) ON DELETE CASCADE,
 remind_at INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
 attempts INTEGER NOT NULL DEFAULT 0, next_attempt INTEGER NOT NULL,
 first_attempt INTEGER, provider_id TEXT, last_error TEXT,
 subject TEXT NOT NULL, body TEXT NOT NULL, action_url TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS reminders_due ON reminders(status,next_attempt);
CREATE TABLE IF NOT EXISTS local_messages (
 id INTEGER PRIMARY KEY, scope TEXT NOT NULL, recipient TEXT NOT NULL,
 subject TEXT NOT NULL, body TEXT NOT NULL, action_url TEXT NOT NULL,
 kind TEXT NOT NULL, created_at INTEGER NOT NULL, message_key TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS rate_limits (
 bucket TEXT PRIMARY KEY, hits INTEGER NOT NULL, expires_at INTEGER NOT NULL
);
