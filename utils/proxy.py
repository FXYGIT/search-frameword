# utils/proxy_provider.py

import httpx

async def get_proxy() -> str:
    """
    向代理池服务请求一个可用代理地址。
    你可以根据实际服务地址修改这里。
    """
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://localhost:5010/get/")  # 示例接口
            resp.raise_for_status()
            return resp.text.strip()
    except Exception as e:
        raise RuntimeError(f"获取代理失败: {e}")
