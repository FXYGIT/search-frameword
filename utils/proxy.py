# utils/proxy_provider.py

import httpx
from utils.loader import get_config

cfg = get_config()

async def get_proxy(return_type="str") -> str:
    """
    向代理池服务请求一个可用代理地址。
    你可以根据实际服务地址修改这里。
    """
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get("http://172.22.121.6:60007/proxy/get/")  # 示例接口
            resp.raise_for_status()

            proxy = resp.json()["proxy"]
            proxy_str = "http://%(user)s:%(pwd)s@%(proxy)s/" % {"user": cfg._config["proxy"]["username"], "pwd": cfg._config["proxy"]["password"], "proxy": proxy}

            if return_type == "str":
                return proxy_str
            elif return_type == "dict":
                return {
                    "http": proxy_str,
                    "https": proxy_str
                }
    except Exception as e:
        raise RuntimeError(f"获取代理失败: {e}")
    
def get_proxy_sync(return_type="str") -> str:
    """
    同步方式向代理池服务请求一个可用代理地址。
    """
    try:
        with httpx.Client(timeout=5) as client:
            resp = client.get("http://172.22.121.6:60007/proxy/get/")
            resp.raise_for_status()
            proxy = resp.json()["proxy"]
            proxy_str = "http://%(user)s:%(pwd)s@%(proxy)s/" % {
                "user": cfg._config["proxy"]["username"],
                "pwd": cfg._config["proxy"]["password"],
                "proxy": proxy
            }
            if return_type == "str":
                return proxy_str
            elif return_type == "dict":
                return {
                    "http": proxy_str,
                    "https": proxy_str
                }
    except Exception as e:
        raise RuntimeError(f"同步获取代理失败: {e}")
