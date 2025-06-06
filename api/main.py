# api/main.py
from fastapi import FastAPI
from api.routes import search
from api.middleware import LoggingMiddleware
from api.ratelimiter import limiter
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

app = FastAPI()
app.include_router(search.router)

# 限速处理
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def ratelimit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"success": False, "error": "Too Many Requests"}
    )

# 中间件
app.add_middleware(LoggingMiddleware)
