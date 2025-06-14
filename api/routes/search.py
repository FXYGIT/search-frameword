# api/routes/search.py
from fastapi import APIRouter, HTTPException, Request, Depends
from models.search import SearchRequest, SearchResponse, SearchResponseBaidu, SearchResponseWeixin
from service.websearch.sougou_weixin import SougouWeixinSearchEngine
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from api.ratelimiter import limiter
from service.websearch.tianyan import TianyanSearchEngine
from service.websearch.tianyan_Selenium import TianyanChaSpider
from service.websearch.driver_manager import SeleniumManager
from service.websearch.asyn_driver_manager import AsyncSeleniumManager
from models.search import SearchResponseTianyan
router = APIRouter()

@router.post("/search", response_model=SearchResponse)
@limiter.limit("100/second")  # 每分钟10次
async def search(
    request: Request,
    body: SearchRequest,
):
    if body.engine == "sougou_weixin":
        engine = SougouWeixinSearchEngine()
        model_cls = SearchResponseWeixin
    elif body.engine == "tianyan_Selenium":
        # 创建AsyncSeleniumManager
        manager = AsyncSeleniumManager(max_drivers=3)
        # 先初始化池
        await manager.initialize()
        
        # 创建爬虫实例
        engine = TianyanChaSpider(manager)
        model_cls = SearchResponseTianyan
        
        try:
            # 调用异步接口方法
            results = await engine.asearch(body.query, manager)
            return model_cls(success=True, data=results)
        except Exception as e:
            return model_cls(success=False, error=str(e))
        
    try:
        results = await engine.asearch(body.query)
        return model_cls(success=True, data=results)
    except Exception as e:
        return model_cls(success=False, error=str(e))
