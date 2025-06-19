# api/main.py
from contextlib import asynccontextmanager
from service.websearch.asyn_driver_manager import init_driver_pool, shutdown_driver_pool
from fastapi import FastAPI
from api.routes import search
from api.ratelimiter import limiter
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from service.proxypool import ProxyPool

@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = ProxyPool()
    await pool.start()
    app.state.proxy_pool = pool
    yield
    await pool.stop()


# app = FastAPI(lifespan=lifespan) # 暂时不考虑试用代理池 隧道代理
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
# app.add_middleware(LoggingMiddleware)

