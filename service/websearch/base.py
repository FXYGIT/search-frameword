# service/websearch/base.py

from abc import ABC, abstractmethod
from typing import List, Optional
import httpx
import logging

from httpx import HTTPStatusError

from tenacity import retry, stop_after_attempt, wait_fixed, RetryError, before_sleep_log



retry_logger = logging.getLogger("tenacity")

from utils.logger import get_logger
from utils.http_client import get_http_client
from utils.proxy import get_proxy
# from service.proxypool import get_proxy



class BaseSearchEngine(ABC):
    """
    抽象搜索引擎基类。
    所有搜索引擎需继承此类，并实现 search 方法。
    """

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    async def asearch(self, query: str) -> List:
        """
        子类必须实现该方法，接收查询参数，返回搜索结果列表。
        """
        pass

    @retry(
        stop=stop_after_attempt(5),
        # wait=wait_fixed(1),  # 每次重试间隔 1 秒，可自定义
        # retry_error_callback=lambda retry_state: None,
        before_sleep=before_sleep_log(retry_logger, logging.WARNING),
    )

    async def fetch(self, url: str, headers: Optional[dict] = None, params: Optional[dict] = None, cookies: Optional[dict] = None) -> Optional[str]:
        try:
            proxy = await get_proxy()
        except Exception as e:
            proxy = None
        client = get_http_client(proxy=proxy)
        self.logger.debug(f"Using proxy: {proxy}")

        try:
            response = await client.get(url, headers=headers, params=params, timeout=10, cookies=cookies)
            response.raise_for_status()
            return response
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            self.logger.warning(f"Fetch failed with proxy {proxy}: {e}")
            raise e  # 告诉 tenacity 触发重试
        finally:
            await client.aclose()






