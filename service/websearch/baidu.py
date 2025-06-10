# service/websearch/baidu.py

from typing import List
from service.websearch.base import BaseSearchEngine
from models.search import SearchBaiduResult
from service.websearch.registry import register_engine


@register_engine("baidu")
class BaiduSearchEngine(BaseSearchEngine):
    """
    百度搜索引擎实现类。
    """

    async def search(self, query: str) -> List[SearchBaiduResult]:
        """
        实现百度搜索的核心逻辑。
        这里只是示例结构，暂不执行实际请求。
        """
        self.logger.info(f"Performing Baidu search for query: {query}")

        # 伪代码结构，后续可以调用 self.fetch() 获取页面内容
        # url = f"https://www.baidu.com/s?wd={query}"
        # html = await self.fetch(url)

        # 暂时返回一个空结果列表
        return []
