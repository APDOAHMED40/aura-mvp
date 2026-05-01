# AI Executive Agent - المدير التنفيذي الذكي

مساعد ذكاء اصطناعي شخصي متكامل يعمل كمدير تنفيذي لحياتك المهنية والشخصية.

## المميزات

- **محادثة ذكية**: تكلم مع المدير التنفيذي بالعربية المصرية أو أي لغة
- **ترجمة احترافية**: ترجمة نصوص بين أي لغتين بدقة عالية
- **كتابة محتوى**: مقالات، أبحاث، إيميلات، محتوى تسويقي
- **ذاكرة طويلة المدى**: يتعلم تفضيلاتك ويتحسن مع الوقت
- **تقارير يومية**: ملخص يومي لكل النشاطات

### قريباً
- تصميم (لوجو، بوستر، سوشيال ميديا)
- إنشاء فيديوهات
- إدارة حسابات سوشيال ميديا
- إعلانات ممولة (Meta Ads)
- أتمتة مهام متكررة

## التثبيت

### المتطلبات
- Python 3.11+
- مفتاح Google Gemini API ([احصل عليه مجاناً](https://aistudio.google.com/apikey))

### خطوات التثبيت

```bash
# 1. انسخ المشروع
git clone https://github.com/YOUR_USERNAME/ai-executive-agent.git
cd ai-executive-agent

# 2. أنشئ بيئة افتراضية
python -m venv venv
source venv/bin/activate  # Linux/Mac
# أو
venv\Scripts\activate  # Windows

# 3. ثبت المكتبات
pip install -e .

# 4. أنشئ ملف الإعدادات
cp .env.example .env
# عدل .env وأضف مفتاح Gemini API

# 5. شغّل التطبيق
python main.py
```

### افتح المتصفح
```
http://localhost:8000
```

## البنية

```
ai-executive-agent/
├── main.py                 # نقطة البداية
├── src/
│   ├── core/
│   │   ├── brain.py        # العقل المركزي (Gemini Agent)
│   │   ├── config.py       # الإعدادات
│   │   └── database.py     # قاعدة البيانات
│   ├── modules/
│   │   ├── translation/    # وحدة الترجمة
│   │   ├── design/         # وحدة التصميم (قريباً)
│   │   ├── video/          # وحدة الفيديو (قريباً)
│   │   ├── social_media/   # وحدة السوشيال ميديا (قريباً)
│   │   ├── ads/            # وحدة الإعلانات (قريباً)
│   │   └── automation/     # وحدة الأتمتة (قريباً)
│   └── web/
│       ├── app.py          # FastAPI Application
│       ├── static/         # CSS, JS, Images
│       └── templates/      # HTML Templates
├── data/                   # قاعدة البيانات
└── logs/                   # السجلات
```

## التقنيات المستخدمة

- **Backend**: FastAPI + Python
- **AI**: Google Gemini 2.0 Flash + LangChain
- **Database**: SQLite (SQLAlchemy async)
- **Frontend**: HTML/CSS/JS (RTL Arabic interface)
- **Real-time**: WebSocket for streaming chat

## الترخيص

MIT License
