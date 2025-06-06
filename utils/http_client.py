# utils/http_client.py

import httpx
from typing import Optional


def get_http_client(proxy: Optional[str] = None) -> httpx.AsyncClient:
    """
    创建支持异步和可选代理的 httpx 客户端。
    """
    proxies = None
    if proxy:
        proxies = {
            "http://": proxy,
            "https://": proxy,
        }

    return httpx.AsyncClient(proxy=proxy)
