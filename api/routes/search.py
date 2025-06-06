# api/routes/search.py
from fastapi import APIRouter, HTTPException, Request, Depends
from models.search import SearchRequest, SearchResponse
from service.websearch.registry import get_engine
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
    try:
        engine = get_engine(body.engine)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        results = await engine.search(body.query)
        return SearchResponse(success=True, data=results)
    except Exception as e:
        return SearchResponse(success=False, error=str(e))
