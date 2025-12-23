## FAST CHAT PIPELINE

FastAPI service that ingests documents, images, and soon video, then serves retrieval-augmented chat via WebSocket.

### Highlights
- WebSocket chat at `/ws/chat/{session_id}` with typing signals and conversation history; helper endpoint `/set-session` and built-in demo page at `/ws-chat-demo`.
- Multimodal ingestion: `/ingest/document` chunks PDF/DOCX text, `/ingest/image` runs OCR and chunks results, `/ingest/video` accepts uploads (pipeline stubbed for future ASR/frame analysis).
- Context persistence backed by Weaviate and Postgres; semantic recall (near-text) feeds the LLM with only highly relevant chunks (distance < 0.5).
- FastAPI lifespan boots the database, reads the OpenAI key from settings, and enables CORS for easy client experimentation.

### Quickstart
- Prereqs: Python 3, local Weaviate and Postgres instances, `OPENAI_API_KEY` (via settings), `pip install -r requirements.txt`.
- Run: `uvicorn app.main:app --reload` from repo root.
- Try: open `http://localhost:8000/ws-chat-demo`, click Start Session, then chat or upload media; health check at `/`.

### API Map
- `GET /`: service banner
- `GET /set-session`: returns a UUID `session_id`
- `WS /ws/chat/{session_id}`: send plain text; receives typing events plus message payload with prior turns
- `POST /ingest/document` (file): parses, chunks, and stores text
- `POST /ingest/image` (file): OCRs, chunks, and stores text
- `POST /ingest/video` (file): validates upload (placeholder response)
