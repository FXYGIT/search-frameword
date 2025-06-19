# api/routes/search.py
from fastapi import APIRouter, HTTPException, Request, Depends
from models.search import SearchRequest, SearchResponse, SearchResponseBaidu, SearchResponseWeixin
from service.websearch.baidu import BaiduSearchEngine
from service.websearch.sougou_weixin import SougouWeixinSearchEngine
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from api.ratelimiter import limiter

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
    if body.engine == "baidu":
        engine = BaiduSearchEngine()
        model_cls = SearchResponseBaidu

    try:
        results = await engine.asearch(body.query)
        return model_cls(success=True, data=results)
    except Exception as e:
        return model_cls(success=False, error=str(e))
