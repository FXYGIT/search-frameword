# api/middleware.py
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import logging

# logger = logging.getLogger("uvicorn.access")


# class LoggingMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request: Request, call_next):
#         start_time = time.time()
#         response = await call_next(request)
#         process_time = time.time() - start_time
#         client_ip = request.client.host
#         logger.info(
#             f"{request.method} {request.url.path} from {client_ip} "
#             f"completed_in={process_time:.2f}s status={response.status_code}"
#         )
#         return response
