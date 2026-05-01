"""
FastAPI Web Application - The main web dashboard and API.
"""

import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from src.core.config import settings
from src.core.database import init_db, async_session, Conversation, Task, Memory
from src.core.brain import brain
from src.modules.translation.translator import translator

from sqlalchemy import select, desc, func


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    await init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


# ─── Web Pages ───────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    summary = {}
    try:
        summary = await brain.get_daily_summary()
    except Exception:
        summary = {
            "date": "",
            "total_messages": 0,
            "user_messages": 0,
            "tasks_total": 0,
            "tasks_completed": 0,
            "tasks_pending": 0,
            "tasks_failed": 0,
        }
    return templates.TemplateResponse(request, "dashboard.html", {
        "summary": summary,
        "app_name": settings.app_name,
    })


@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse(request, "chat.html", {
        "app_name": settings.app_name,
    })


@app.get("/tasks", response_class=HTMLResponse)
async def tasks_page(request: Request):
    async with async_session() as session:
        result = await session.execute(
            select(Task).order_by(desc(Task.created_at)).limit(50)
        )
        tasks = result.scalars().all()
    return templates.TemplateResponse(request, "tasks.html", {
        "tasks": tasks,
        "app_name": settings.app_name,
    })


@app.get("/translate", response_class=HTMLResponse)
async def translate_page(request: Request):
    return templates.TemplateResponse(request, "translate.html", {
        "app_name": settings.app_name,
    })


@app.get("/memories", response_class=HTMLResponse)
async def memories_page(request: Request):
    async with async_session() as session:
        result = await session.execute(
            select(Memory).order_by(desc(Memory.importance)).limit(50)
        )
        memories = result.scalars().all()
    return templates.TemplateResponse(request, "memories.html", {
        "memories": memories,
        "app_name": settings.app_name,
    })


# ─── API Endpoints ───────────────────────────────────────────────────────────

@app.post("/api/chat")
async def api_chat(request: Request):
    data = await request.json()
    message = data.get("message", "")
    if not message:
        return {"error": "الرسالة فاضية"}

    try:
        response = await brain.process_message(message)
        return {"response": response, "status": "ok"}
    except ValueError as e:
        return {"error": str(e), "status": "error"}
    except Exception as e:
        return {"error": f"حصل خطأ: {str(e)}", "status": "error"}


@app.post("/api/translate")
async def api_translate(request: Request):
    data = await request.json()
    text = data.get("text", "")
    target = data.get("target_language", "")
    source = data.get("source_language")

    if not text or not target:
        return {"error": "النص واللغة المستهدفة مطلوبين"}

    try:
        result = await translator.translate(text, target, source)
        return {"result": result, "status": "ok"}
    except Exception as e:
        return {"error": f"حصل خطأ: {str(e)}", "status": "error"}


@app.post("/api/proofread")
async def api_proofread(request: Request):
    data = await request.json()
    text = data.get("text", "")
    language = data.get("language")

    if not text:
        return {"error": "النص مطلوب"}

    try:
        result = await translator.proofread(text, language)
        return {"result": result, "status": "ok"}
    except Exception as e:
        return {"error": f"حصل خطأ: {str(e)}", "status": "error"}


@app.get("/api/summary")
async def api_summary():
    try:
        summary = await brain.get_daily_summary()
        return {"summary": summary, "status": "ok"}
    except Exception as e:
        return {"error": str(e), "status": "error"}


@app.get("/api/history")
async def api_history(limit: int = 50):
    async with async_session() as session:
        result = await session.execute(
            select(Conversation)
            .order_by(desc(Conversation.created_at))
            .limit(limit)
        )
        rows = result.scalars().all()
        rows.reverse()
        return {
            "history": [
                {
                    "role": r.role,
                    "content": r.content,
                    "module": r.module,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ],
            "status": "ok",
        }


# ─── WebSocket for real-time streaming chat ───────────────────────────────────

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            user_message = msg.get("message", "")

            if not user_message:
                await websocket.send_json({"type": "error", "content": "الرسالة فاضية"})
                continue

            await websocket.send_json({"type": "start"})

            try:
                full_response = ""
                async for chunk in brain.process_message_stream(user_message):
                    full_response += chunk
                    await websocket.send_json({"type": "chunk", "content": chunk})

                await websocket.send_json({"type": "end", "content": full_response})
            except ValueError as e:
                await websocket.send_json({
                    "type": "error",
                    "content": f"خطأ: {str(e)}. تأكد من إضافة مفتاح Google Gemini API.",
                })
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "content": f"حصل خطأ: {str(e)}",
                })

    except WebSocketDisconnect:
        pass
