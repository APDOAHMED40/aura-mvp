"""
Core Brain - The central AI agent that understands commands and delegates to modules.
Uses Google Gemini as the LLM backbone.
"""

import json
import datetime
from typing import AsyncGenerator

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import async_session, Conversation, Memory, Task


SYSTEM_PROMPT = """أنت "المدير التنفيذي الذكي" - مساعد AI شخصي متكامل يعمل كمدير تنفيذي لحياة المستخدم المهنية والشخصية.

## شخصيتك:
- تتكلم بالعربية المصرية بشكل طبيعي وودود
- محترف وذكي ودقيق في الشغل
- بتطلب إذن قبل أي عملية مهمة
- بتدي تقارير واضحة ومنظمة
- بتتعلم من أخطائك وتتحسن مع الوقت

## قدراتك (الوحدات المتاحة):
1. **الترجمة** (translation): ترجمة نصوص ومستندات بين أي لغتين
2. **كتابة المحتوى** (content): كتابة مقالات، أبحاث، إيميلات، محتوى تسويقي
3. **التصميم** (design): تصميم لوجو، بوستر، بوستات سوشيال ميديا (قريباً)
4. **الفيديو** (video): إنشاء فيديوهات سوشيال ميديا ويوتيوب (قريباً)
5. **السوشيال ميديا** (social): إدارة حسابات ونشر محتوى (قريباً)
6. **الإعلانات** (ads): إدارة حملات إعلانية ممولة (قريباً)
7. **الأتمتة** (automation): أتمتة مهام متكررة (قريباً)
8. **الأبحاث** (research): البحث وجمع المعلومات من الإنترنت

## قواعد مهمة:
- **دايماً** اطلب إذن المستخدم قبل أي عملية تنفيذية
- لو مش متأكد من حاجة، اسأل
- قدّم اقتراحات وحلول بديلة
- اعترف بأخطائك وتعلم منها
- لو مهارة جديدة مطلوبة، قول إنك هتتعلمها

## تنسيق الردود:
- استخدم Markdown للتنسيق
- كن مختصر ومفيد
- استخدم القوائم والجداول عند الحاجة

عند تحليل طلب المستخدم، حدد:
1. الوحدة المناسبة (module)
2. المهمة المطلوبة (task)
3. هل تحتاج إذن؟ (needs_approval)

رد دايماً بصيغة JSON في نهاية ردك بهذا الشكل (بين علامات ```json و```):
```json
{
    "module": "اسم_الوحدة",
    "task": "وصف_المهمة",
    "needs_approval": true/false,
    "can_execute": true/false
}
```

لو الطلب مجرد سؤال أو محادثة عادية، استخدم:
```json
{
    "module": "chat",
    "task": "محادثة",
    "needs_approval": false,
    "can_execute": true
}
```
"""


class Brain:
    def __init__(self):
        self.llm = None
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return
        if not settings.google_gemini_api_key:
            raise ValueError("GOOGLE_GEMINI_API_KEY is not set")
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=settings.google_gemini_api_key,
            temperature=0.7,
            max_output_tokens=4096,
        )
        self._initialized = True

    async def _load_conversation_history(self, limit: int = 20) -> list:
        async with async_session() as session:
            result = await session.execute(
                select(Conversation)
                .order_by(desc(Conversation.created_at))
                .limit(limit)
            )
            rows = result.scalars().all()
            rows.reverse()

            messages = []
            for row in rows:
                if row.role == "user":
                    messages.append(HumanMessage(content=row.content))
                elif row.role == "assistant":
                    messages.append(AIMessage(content=row.content))
            return messages

    async def _load_memories(self) -> str:
        async with async_session() as session:
            result = await session.execute(
                select(Memory)
                .order_by(desc(Memory.importance))
                .limit(20)
            )
            memories = result.scalars().all()
            if not memories:
                return ""

            memory_text = "\n## ذاكرتك (ما تعلمته سابقاً):\n"
            for mem in memories:
                memory_text += f"- [{mem.category}] {mem.key}: {mem.value}\n"
            return memory_text

    async def _save_conversation(self, role: str, content: str, module: str | None = None):
        async with async_session() as session:
            conv = Conversation(role=role, content=content, module=module)
            session.add(conv)
            await session.commit()

    async def _save_memory(self, category: str, key: str, value: str, importance: int = 5):
        async with async_session() as session:
            existing = await session.execute(
                select(Memory).where(Memory.key == key)
            )
            mem = existing.scalar_one_or_none()
            if mem:
                mem.value = value
                mem.importance = importance
                mem.updated_at = datetime.datetime.utcnow()
            else:
                mem = Memory(category=category, key=key, value=value, importance=importance)
                session.add(mem)
            await session.commit()

    async def process_message(self, user_message: str) -> str:
        await self.initialize()

        history = await self._load_conversation_history()
        memories = await self._load_memories()

        system_content = SYSTEM_PROMPT
        if memories:
            system_content += memories

        messages = [SystemMessage(content=system_content)]
        messages.extend(history)
        messages.append(HumanMessage(content=user_message))

        await self._save_conversation("user", user_message)

        response = await self.llm.ainvoke(messages)
        response_text = response.content

        module = self._extract_module(response_text)
        await self._save_conversation("assistant", response_text, module=module)

        return response_text

    async def process_message_stream(self, user_message: str) -> AsyncGenerator[str, None]:
        await self.initialize()

        history = await self._load_conversation_history()
        memories = await self._load_memories()

        system_content = SYSTEM_PROMPT
        if memories:
            system_content += memories

        messages = [SystemMessage(content=system_content)]
        messages.extend(history)
        messages.append(HumanMessage(content=user_message))

        await self._save_conversation("user", user_message)

        full_response = ""
        async for chunk in self.llm.astream(messages):
            if chunk.content:
                full_response += chunk.content
                yield chunk.content

        module = self._extract_module(full_response)
        await self._save_conversation("assistant", full_response, module=module)

    def _extract_module(self, response: str) -> str | None:
        try:
            json_start = response.rfind("```json")
            if json_start == -1:
                return None
            json_end = response.find("```", json_start + 7)
            if json_end == -1:
                return None
            json_str = response[json_start + 7:json_end].strip()
            data = json.loads(json_str)
            return data.get("module")
        except (json.JSONDecodeError, ValueError):
            return None

    async def get_daily_summary(self) -> dict:
        async with async_session() as session:
            today = datetime.date.today().isoformat()

            conversations = await session.execute(
                select(Conversation).where(
                    Conversation.created_at >= datetime.datetime.combine(
                        datetime.date.today(), datetime.time.min
                    )
                )
            )
            convs = conversations.scalars().all()

            tasks = await session.execute(
                select(Task).where(
                    Task.created_at >= datetime.datetime.combine(
                        datetime.date.today(), datetime.time.min
                    )
                )
            )
            task_list = tasks.scalars().all()

            return {
                "date": today,
                "total_messages": len(convs),
                "user_messages": len([c for c in convs if c.role == "user"]),
                "tasks_total": len(task_list),
                "tasks_completed": len([t for t in task_list if t.status == "done"]),
                "tasks_pending": len([t for t in task_list if t.status == "pending"]),
                "tasks_failed": len([t for t in task_list if t.status == "failed"]),
            }


brain = Brain()
