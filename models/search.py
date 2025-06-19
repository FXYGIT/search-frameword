from pydantic import BaseModel
from typing import List, Optional, Union


class SearchRequest(BaseModel):
    query: str
    engine: str  # 比如 "baidu", "google"


class SearchBaiduResult(BaseModel):
    title: str
    # 将这些字段标记为可选，允许为空
    # organization: Optional[str] = None
    # publish_time: Optional[str] = None
    # location: Optional[str] = None
    content: str
    md5: str


class SearchSougouWeixinResult(BaseModel):
    title: str
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
