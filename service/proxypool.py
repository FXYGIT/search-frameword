import time
import asyncio
from typing import Dict, Optional, List
import httpx
import hashlib

from models.proxypool import Proxy
from utils.loader import get_config
cfg = get_config()


async def get_proxy() -> str:
    """模块级别便捷函数"""
    return await ProxyPool().get_proxy()


class ProxyPool:
    _instance: Optional["ProxyPool"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True

        self._pool: Dict[str, Proxy] = {}
        # self._lock = asyncio.Lock()
        # self._fetching = False
        # self._fetch_event = asyncio.Event()
        # self._fetch_event.set()  # 初始设置为完成状态
        self._req_timestamps: asyncio.Queue = asyncio.Queue()
        self._scheduler_task: Optional[asyncio.Task] = None
        self._stop = False
        self._daily_taken = 0

        # 参数配置
        self.WINDOW = 10.0
        self.REUSE_FACTOR = 10
        self.MAX_POOL_SIZE = 20
        self.MIN_POOL_SIZE = 3
        self.PROXY_EXPIRE = 50.0

    async def start(self):
        if self._scheduler_task is None:
            self._stop = False
            self._scheduler_task = asyncio.create_task(self._scheduler())

    async def stop(self):
        self._stop = True
        if self._scheduler_task:
            await self._scheduler_task
            self._scheduler_task = None

    async def _scheduler(self):
        while not self._stop:
            await asyncio.sleep(1)

            # 清理过期、统计速率、决定是否 fetch
            to_fetch = 0

            # 清理过期代理
            now = time.time()
            expired_keys = [k for k, v in self._pool.items() if v.age >= self.PROXY_EXPIRE]
            for k in expired_keys:
                del self._pool[k]

            # 清理过期请求记录
            while not self._req_timestamps.empty() and now - self._req_timestamps._queue[0] > self.WINDOW:
                await self._req_timestamps.get()

            rps = self._req_timestamps.qsize() / self.WINDOW
            desired_pool_size = max(self.MIN_POOL_SIZE, int(rps / self.REUSE_FACTOR * 1.2))
            desired_pool_size = min(self.MAX_POOL_SIZE, desired_pool_size)
            current_pool_size = len(self._pool)

            to_fetch = desired_pool_size - current_pool_size

            if to_fetch > 0:
                await self._fetch_proxies(to_fetch)

    async def _fetch_proxies(self, batch: int):
        can_take = min(batch, 10000 - self._daily_taken)
        if can_take <= 0:
            return

        api_key = "a7708f336b18445fa0d9b41a1220e4be"
        params = {
            "auto_white": 1,
            "ip_remain": 1,
            "num": can_take,
            "pt": 1,
            "result_type": "json2", 
            "trade_no": "5719560476590361",
        }
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        sign_str = "&".join(f"{k}={v}" for k, v in sorted_params) + f"&key={api_key}"
        params["sign"] = hashlib.md5(sign_str.encode('utf-8')).hexdigest()

        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get("http://v2.api.juliangip.com/unlimited/getips", params=params)
                resp.raise_for_status()
                proxy_list = resp.json()["data"]["proxy_list"]
        except Exception as e:
            print(f"[ProxyPool] 获取代理失败: {e}")
            return

        for data in proxy_list:
            proxy_str = f"http://{cfg._config['proxy']['username']}:{cfg._config['proxy']['password']}@{data['ip']}:{data['port']}/"
            self._pool[proxy_str] = Proxy(proxy_str=proxy_str)
        self._daily_taken += len(proxy_list)

    async def get_proxy(self) -> str:
        while True:
            if self._pool:
                proxy = sorted(self._pool.values(), key=lambda e: (e.use_count, -e.ttl_left))[0]
                await self._req_timestamps.put(time.time())
                return proxy.proxy_str

            await self._req_timestamps.put(time.time())
            await asyncio.sleep(1)