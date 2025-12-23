CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgai;


CREATE TABLE chat_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);


CREATE TABLE sources (
  id UUID PRIMARY KEY,
  source_type TEXT NOT NULL CHECK (source_type IN ('document', 'image', 'video')),
  filename TEXT,
  mime_type TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);


CREATE TABLE context_chunks (
  id UUID PRIMARY KEY,
  source_id UUID REFERENCES sources(id) ON DELETE CASCADE,
  source_type TEXT NOT NULL,  
  -- Text used for embeddings + RAG
  content TEXT NOT NULL,
  -- Document metadata
  page_number INTEGER,
  -- Video metadata
  start_time_sec FLOAT,
  end_time_sec FLOAT,
  created_at TIMESTAMPTZ DEFAULT now()
);


CREATE INDEX context_chunks_embedding_idx
ON context_chunks
USING hnsw (embedding vector_cosine_ops);


CREATE INDEX context_chunks_source_type_idx
ON context_chunks (source_type);


CREATE INDEX context_chunks_source_id_idx
ON context_chunks (source_id);
