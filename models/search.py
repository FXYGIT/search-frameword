from pydantic import BaseModel
from typing import List, Optional


class SearchRequest(BaseModel):
    query: str
    engine: str  # 比如 "baidu", "google"


class SearchResult(BaseModel):
    title: str
    link: str
    detail_content: str


class SearchResponse(BaseModel):
    success: bool
    data: Optional[List[SearchResult]] = None
    error: Optional[str] = None
