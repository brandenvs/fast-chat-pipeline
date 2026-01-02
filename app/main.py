from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from uuid import uuid4

from app.storage.db_helper import init_db
from app.core import settings
# from storage.init_db import init_db

from app.ws.chat import handle_chat_message

from app.ingestion.video import router as video_router
from app.ingestion.image import router as image_router
from app.ingestion.document import router as document_router

# Lifespan (startup/shutdown)
@asynccontextmanager
async def lifespan(app: FastAPI):
    _ = settings.settings.openai_api_key 
    await init_db()
    yield

# App
app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(video_router)
app.include_router(image_router)
app.include_router(document_router)

html = """
<!DOCTYPE html>
<html>
  <head>
    <title>Chat</title>

    <!-- Markdown renderer -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>

    <style>
      body {
        font-family: Arial, sans-serif;
        max-width: 800px;
        margin: 40px auto;
      }
      #chat {
        border: 1px solid #ddd;
        padding: 12px;
        height: 300px;
        overflow-y: auto;
        margin-bottom: 10px;
      }
      .msg {
        margin-bottom: 8px;
        padding: 6px 10px;
        border-radius: 6px;
        max-width: 80%;
        white-space: normal;
      }
      .user {
        background: #d9f1ff;
        margin-left: auto;
      }
      .assistant {
        background: #f1f1f1;
        margin-right: auto;
      }
      .row {
        display: flex;
      }
      .panel {
        border: 1px solid #ddd;
        padding: 10px;
        margin-top: 20px;
      }
      .panel h3 {
        margin-top: 0;
      }
      pre {
        background: #222;
        color: #eee;
        padding: 8px;
        border-radius: 4px;
        font-size: 12px;
        overflow-x: auto;
      }
      code {
        font-family: monospace;
      }
    </style>
  </head>

  <body>
    <h1>Chat bot websocket TEST</h1>

    <button onclick="startSession()">Start Session</button>

    <div id="chat"></div>

    <div id="typing" style="display:none; font-style:italic;">
      Bot is typing...
    </div>

    <form onsubmit="sendMessage(event)">
      <input type="text" id="messageText" autocomplete="off" style="width:80%;" />
      <button>Send</button>
    </form>

    <!-- ======================= -->
    <!-- Ingestion Test Panel -->
    <!-- ======================= -->
    <div class="panel">
      <h3>Media Ingestion Test</h3>

      <div>
        <strong>Document (PDF / DOCX)</strong><br />
        <input type="file" id="docFile" />
        <button onclick="uploadFile('document', 'docFile')">Upload</button>
      </div>

      <br />

      <div>
        <strong>Image (PNG / JPG)</strong><br />
        <input type="file" id="imageFile" />
        <button onclick="uploadFile('image', 'imageFile')">Upload</button>
      </div>

      <br />

      <div>
        <strong>Video (MP4)</strong><br />
        <input type="file" id="videoFile" />
        <button onclick="uploadFile('video', 'videoFile')">Upload</button>
      </div>

      <h4>Upload Response</h4>
      <pre id="uploadResult">No uploads yet</pre>
    </div>

    <script>
      let ws = null;
      let sessionId = null;
      let renderedCount = 0;

      async function startSession() {
        const res = await fetch("/set-session");
        const data = await res.json();
        sessionId = data.session_id;

        ws = new WebSocket(`ws://localhost:8000/ws/chat/${sessionId}`);

        ws.onopen = () => console.log("WS connected", sessionId);
        ws.onclose = e => console.log("WS closed", e.code);

        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);

          if (data.type === "typing") {
            document.getElementById("typing").style.display =
              data.value ? "block" : "none";
            return;
          }

          if (data.type === "message") {
            renderChat(data.payload);
          }
        };
      }

      function renderChat(payload) {
        const chat = document.getElementById("chat");

        payload.previousMessages
          .slice(renderedCount)
          .forEach(msg => addMessage(msg.role, msg.content));

        renderedCount = payload.previousMessages.length;
        chat.scrollTop = chat.scrollHeight;
      }

      function addMessage(role, content) {
        const chat = document.getElementById("chat");

        const row = document.createElement("div");
        row.className = "row";

        const div = document.createElement("div");
        div.className = `msg ${role}`;

        if (role === "assistant") {
          // Render markdown safely
          div.innerHTML = marked.parse(content);
        } else {
          // User messages stay plain text
          div.textContent = content;
        }

        row.appendChild(div);
        chat.appendChild(row);
      }

      function sendMessage(event) {
        event.preventDefault();
        if (!ws || ws.readyState !== WebSocket.OPEN) {
          alert("Start a session first");
          return;
        }
        const input = document.getElementById("messageText");
        ws.send(input.value);
        input.value = "";
      }

      async function uploadFile(type, inputId) {
        const input = document.getElementById(inputId);
        if (!input.files.length) {
          alert("Select a file first");
          return;
        }

        const file = input.files[0];
        const formData = new FormData();
        formData.append("file", file);

        const res = await fetch(`/ingest/${type}`, {
          method: "POST",
          body: formData
        });

        const data = await res.json();
        document.getElementById("uploadResult").textContent =
          JSON.stringify(data, null, 2);
      }
    </script>
  </body>
</html>
"""


# Routes
@app.get("/ws-chat-demo")
async def ws_chat_demo():
    return HTMLResponse(html)

@app.get("/set-session")
def set_session():
    session_id = str(uuid4())
    return {"session_id": session_id}

@app.websocket("/ws/chat/{session_id}")
async def websocket_chat(ws: WebSocket, session_id: str):
    await ws.accept()
    try:
        while True:
            msg = await ws.receive_text()
            await ws.send_json({
                "type": "typing",
                "value": True
            })
            reply = await handle_chat_message(session_id, msg)
            await ws.send_json({
                "type": "typing",
                "value": False
            })
            await ws.send_json({
                "type": "message",
                "payload": reply
            })

    except WebSocketDisconnect:
        print("Disconnected:", session_id)

@app.get("/")
async def root():
    return {"message": "Chat Pipeline - host"}
