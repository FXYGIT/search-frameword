# app.py
import uvicorn
from utils.loader import get_config

cfg = get_config()

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host=cfg.get("app.host", "0.0.0.0"),
        port=cfg.get("app.port", 8000),
        reload=cfg.get("app.reload", False),
    )
