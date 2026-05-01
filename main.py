"""
AI Executive Agent - Main Entry Point
"""

import uvicorn
from src.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "src.web.app:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
    )
