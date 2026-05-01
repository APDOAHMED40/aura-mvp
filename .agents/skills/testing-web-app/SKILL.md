# Testing the AI Executive Agent Web App

## Prerequisites

### Devin Secrets Needed
- `GOOGLE_GEMINI_API_KEY` - Required for testing AI-powered features (chat, translation). Get from https://aistudio.google.com/apikey. Without this key, chat and translation will show error messages but all UI/navigation can still be tested.

## Environment Setup

1. Activate the virtual environment and install dependencies:
   ```bash
   cd /home/ubuntu/repos/ai-executive-agent
   python -m venv venv
   source venv/bin/activate
   pip install -e .
   ```

2. Start the server (with or without API key):
   ```bash
   # With API key for full testing:
   GOOGLE_GEMINI_API_KEY=$GOOGLE_GEMINI_API_KEY python main.py

   # Without API key (UI-only testing):
   GOOGLE_GEMINI_API_KEY="" python -c "import uvicorn; uvicorn.run('src.web.app:app', host='0.0.0.0', port=8000, reload=False)"
   ```

3. If port 8000 is already in use:
   ```bash
   fuser -k 8000/tcp
   ```

## App Architecture

- **Backend**: FastAPI (Python) with WebSocket support
- **Frontend**: Server-rendered Jinja2 templates with RTL Arabic dark theme
- **Database**: SQLite via SQLAlchemy async (auto-created at `data/agent.db`)
- **AI**: Google Gemini 2.0 Flash via LangChain

## Available Pages & Routes

| Page | Route | Key Features |
|---|---|---|
| Dashboard | `/` | Welcome card, 4 stat cards, 6 module cards |
| Chat | `/chat` | WebSocket streaming chat (ws://host/ws/chat) |
| Translation | `/translate` | Dual-panel translate with 13 languages |
| Tasks | `/tasks` | Task list (empty state when no tasks) |
| Memories | `/memories` | Memory/learning storage (empty state initially) |

## API Endpoints

- `POST /api/chat` - Sync chat (fallback)
- `POST /api/translate` - Translation
- `POST /api/proofread` - Grammar checking
- `GET /api/summary` - Dashboard stats
- `GET /api/history` - Conversation history
- `WS /ws/chat` - Streaming chat via WebSocket

## Test Flows

### Without API Key (UI Testing)
1. Dashboard: Verify welcome card, stat cards (all 0), module cards (2 "متاح", 4 "قريباً"), sidebar on right (RTL)
2. Chat: Send message → expect error: "خطأ: GOOGLE_GEMINI_API_KEY is not set. تأكد من إضافة مفتاح Google Gemini API."
3. Translation: Type text, click ترجم → expect error in output panel
4. Tasks/Memories: Verify empty state messages
5. Navigation: All 5 sidebar links work, active page highlighted

### With API Key (Full Testing)
1. Chat: Send Arabic message → expect streaming Gemini response in Arabic
2. Translation: Type Arabic text → translate to English → verify output
3. Proofread: Type text with errors → click تدقيق لغوي → verify corrections
4. Dashboard stats: After chatting, verify message count increases
5. History: After chatting, verify /api/history returns saved conversations

## Known Issues & Tips

- The chat textarea uses a custom `handleKeyDown` handler. Pressing Enter alone may add a newline. Click the send button (paper plane icon) to reliably send messages.
- Translation error messages expose raw Pydantic validation errors instead of user-friendly Arabic messages (unlike the chat error handler which is more polished).
- The server might leave processes on port 8000 from previous runs. Always check with `fuser 8000/tcp` before starting.
- The `main.py` entry point uses `uvicorn.run()` directly. For testing, you can also run via the module path: `uvicorn src.web.app:app --host 0.0.0.0 --port 8000`.
- Database is auto-created on first startup. Delete `data/agent.db` to reset all data.
