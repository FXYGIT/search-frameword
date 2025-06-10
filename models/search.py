from pydantic import BaseModel
from typing import List, Optional, Union


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
    md5: str


class SearchResponseBaidu(BaseModel):
    success: bool
    data: Optional[List[SearchBaiduResult]] = None
    error: Optional[str] = None


class SearchResponseWeixin(BaseModel):
    success: bool
    data: Optional[List[SearchSougouWeixinResult]] = None
    error: Optional[str] = None


SearchResponse = Union[SearchResponseBaidu, SearchResponseWeixin]
