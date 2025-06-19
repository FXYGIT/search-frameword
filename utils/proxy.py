import httpx

from utils.loader import get_config
cfg = get_config()

async def get_proxy(return_type="str") -> str:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            proxyUrl = "http://%(user)s:%(password)s@%(server)s" % {
                "user": cfg._config["proxy"]["authKey"],
                "password": cfg._config["proxy"]["password"],
                "server": cfg._config["proxy"]["proxyAddr"],
                }

            proxies = {"http": proxyUrl, "https": proxyUrl}

            return proxyUrl if return_type == "str" else proxies

    except Exception as e:
        raise RuntimeError(f"获取代理失败: {e}")
