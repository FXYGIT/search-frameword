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

# 添加到 models/search.py 文件中

class SearchTianyanResult(BaseModel):
    """天眼查搜索结果模型"""
    company_name: str
    company_type: Optional[List[str]] = None  # 公司类型列表
    company_status: Optional[str] = None
    unified_code: Optional[str] = None  # 统一社会信用代码
    business_scope: Optional[str] = None
    address: Optional[str] = None
    contact: Optional[str] = None
    website: Optional[str] = None
    company_link: Optional[str] = None  # 公司详情页链接

class SearchResponseTianyan(BaseModel):
    """天眼查搜索响应模型"""
    success: bool
    data: Optional[List[SearchTianyanResult]] = None
    error: Optional[str] = None

class SearchResponseBaidu(BaseModel):
    success: bool
    data: Optional[List[SearchBaiduResult]] = None
    error: Optional[str] = None


class SearchResponseWeixin(BaseModel):
    success: bool
    data: Optional[List[SearchSougouWeixinResult]] = None
    error: Optional[str] = None


SearchResponse = Union[SearchResponseBaidu, SearchResponseWeixin, SearchResponseTianyan]
