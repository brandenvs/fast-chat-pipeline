CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,               -- "user" | "assistant" | "system"
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_chat_session
ON chat_messages (session_id, created_at);

DROP TABLE context_chunks;

CREATE TABLE IF NOT EXISTS context_chunks (
  source_id TEXT PRIMARY KEY,
  source_type TEXT NOT NULL,
  content TEXT NOT NULL,
  page_number INTEGER,
  keywords TEXT NOT NULL,
  typical_questions TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_document_chunks_source
ON document_chunks (source_id);
