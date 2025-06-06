from pydantic import BaseModel
from typing import List, Optional


class SearchRequest(BaseModel):
    query: str
    engine: str  # 比如 "baidu", "google"


class SearchBaiduResult(BaseModel):
    title: str
    link: str
    content: str


class SearchSougouWeixinResult(BaseModel):
    title: str
    organization: str
    publish_time: str
    location: str
    content: str


class SearchResponse(BaseModel):
    success: bool
    data: Optional[List[SearchBaiduResult|SearchSougouWeixinResult]] = None
    error: Optional[str] = None 
