"""
Translation Module - Handles text translation between languages using Gemini.
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from src.core.config import settings


TRANSLATION_PROMPT = """أنت مترجم محترف. ترجم النص التالي بدقة عالية مع الحفاظ على:
- المعنى الأصلي
- الأسلوب والنبرة
- التنسيق والفقرات
- المصطلحات التخصصية

إذا لم يتم تحديد اللغة المصدر، حددها تلقائياً.
لا تضف أي تعليقات أو ملاحظات - فقط الترجمة.
"""


class TranslationModule:
    def __init__(self):
        self.llm = None

    async def initialize(self):
        if self.llm:
            return
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=settings.google_gemini_api_key,
            temperature=0.3,
            max_output_tokens=8192,
        )

    async def translate(
        self,
        text: str,
        target_language: str,
        source_language: str | None = None,
    ) -> dict:
        await self.initialize()

        prompt = f"""ترجم النص التالي إلى {target_language}"""
        if source_language:
            prompt += f" (من {source_language})"
        prompt += f":\n\n{text}"

        messages = [
            SystemMessage(content=TRANSLATION_PROMPT),
            HumanMessage(content=prompt),
        ]

        response = await self.llm.ainvoke(messages)

        return {
            "original": text,
            "translated": response.content,
            "source_language": source_language or "auto-detected",
            "target_language": target_language,
        }

    async def detect_language(self, text: str) -> str:
        await self.initialize()
        messages = [
            HumanMessage(
                content=f"حدد لغة النص التالي. رد باسم اللغة فقط بالعربية:\n\n{text}"
            ),
        ]
        response = await self.llm.ainvoke(messages)
        return response.content.strip()

    async def proofread(self, text: str, language: str | None = None) -> dict:
        await self.initialize()
        prompt = "راجع النص التالي لغوياً وصحح الأخطاء"
        if language:
            prompt += f" (اللغة: {language})"
        prompt += f". قدم النص المصحح ثم قائمة بالأخطاء:\n\n{text}"

        messages = [HumanMessage(content=prompt)]
        response = await self.llm.ainvoke(messages)

        return {
            "original": text,
            "corrected": response.content,
            "language": language or "auto-detected",
        }


translator = TranslationModule()
