from fastapi import FastAPI, Request, HTTPException
import os, time, uuid
from pydantic import BaseModel
from typing import Dict
import uvicorn

app = FastAPI()
JOBS: Dict[str, dict] = {}

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "hooksecret")  # غيّره في Render

class Command(BaseModel):
    text: str
    source: str = "web"
    sensitive: bool = False

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/api/commands")
async def create_command(cmd: Command):
    job_id = str(uuid.uuid4())[:8]
    plan = make_plan(cmd.text)
    JOBS[job_id] = {
        "id": job_id,
        "text": cmd.text,
        "plan": plan,
        "status": "queued",
        "created_at": int(time.time()),
        "source": cmd.source,
        "result_url": None,
        "logs": []
    }
    return {"jobId": job_id, "plan": plan, "requiresApproval": False}

@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    return job

@app.post("/webhooks/telegram/{secret}")
async def telegram_webhook(secret: str, request: Request):
    if TELEGRAM_WEBHOOK_SECRET and secret != TELEGRAM_WEBHOOK_SECRET:
        raise HTTPException(403, "forbidden")

    update = await request.json()
    message = update.get("message") or update.get("edited_message")
    if not message:
        return {"ok": True}

    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    if text.startswith("/start"):
        await send_telegram(chat_id, "أهلاً! أنا AURA. اكتب طلبك مثلاً:\nAURA: اعمل عرض عن SQL (10 شرائح)")
    else:
        job_id = str(uuid.uuid4())[:8]
        plan = make_plan(text)
        JOBS[job_id] = {
            "id": job_id,
            "text": text,
            "plan": plan,
            "status": "queued",
            "created_at": int(time.time()),
            "source": "telegram",
            "result_url": None,
            "logs": []
        }
        await send_telegram(chat_id, f"تم تسجيل طلبك ✅\n- Job: {job_id}\n- الخطة: {plan}\nسأبلغك عند الانتهاء.")
    return {"ok": True}

async def send_telegram(chat_id: int, text: str):
    import httpx
    if not TELEGRAM_BOT_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(url, json={"chat_id": chat_id, "text": text})

def make_plan(text: str) -> str:
    t = text.lower()
    if "عرض" in t or "powerpoint" in t:
        return "توليد محتوى شرائح -> إنشاء ملف PPTX -> رفع الملف -> إرجاع الرابط"
    if "workflow" in t or "n8n" in t:
        return "تشغيل workflow على n8n -> استرجاع تقرير التنفيذ"
    if "بوست" in t أو "facebook" in t:
        return "تجهيز نص وصورة -> النشر على فيسبوك -> إرجاع رابط المنشور"
    return "تحليل الطلب -> تمريره للوكيل المناسب -> تنفيذ وإرجاع النتائج"

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
