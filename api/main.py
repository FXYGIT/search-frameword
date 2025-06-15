# api/main.py
from contextlib import asynccontextmanager
from service.websearch.asyn_driver_manager import init_driver_pool, shutdown_driver_pool
from fastapi import FastAPI
from api.routes import search
from api.ratelimiter import limiter
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

app = FastAPI()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时运行
    await init_driver_pool()
    yield
    # 关闭时运行
    await shutdown_driver_pool()

app = FastAPI(lifespan=lifespan)
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
# app.add_middleware(LoggingMiddleware)
