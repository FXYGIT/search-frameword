# service/websearch/sougou_weixin.py

import hashlib

from typing import List
from datetime import datetime
from service.websearch.base import BaseSearchEngine
from models.search import SearchSougouWeixinResult
from service.websearch.registry import register_engine


@register_engine("sougou_weixin")
class SougouWeixinSearchEngine(BaseSearchEngine):
    """
    搜狗微信搜索引擎实现类。
    """

    async def asearch(self, query: str) -> List[SearchSougouWeixinResult]:
        """
        实现百度搜索的核心逻辑。
        这里只是示例结构，暂不执行实际请求。
        """
        self.logger.info(f"Performing SougouWeixin search for query: {query}")

        try:
            links = _search(company_name, 1, hashing_set)
        except Exception as e:
            logger.error(f"{company_name} 搜索失败")
            return []

        datas = []
        for link in links:
            try:
                if link and link[:4] == "http":
                    data = get_detail(link, company_name, company_id)
                else:
                    continue
            except Exception as e:
                continue
            if data:
                datas.append(data)
        logger.info(f"{company_name} 搜索完成，共获取新闻 {len(datas)} 条")

        # 伪代码结构，后续可以调用 self.fetch() 获取页面内容
        # url = f"https://www.baidu.com/s?wd={query}"
        # html = await self.fetch(url)

        # 暂时返回一个空结果列表
        return []


    def _search(query, page, hashing_set):
        proxies = get_proxy()
        params = {
            "type": 2,
            "s_from": "input",
            "query": f'"{query}"',
            "ie": "utf8",
            "page": page
        }
        response = requests.get('https://weixin.sogou.com/weixin', params=params, headers=headers_search, timeout=5, proxies=proxies)
        cookies = response.cookies.get_dict()
        tree = html.fromstring(response.text)

        filter_num = 0
        sougou_links = []
        for element in tree.xpath("//ul[@class='news-list']/li"):
            link = "https://weixin.sogou.com"+element.xpath("./div[@class='txt-box']/h3/a/@href")[0]
            title = "".join([text.replace("\n", "").strip() for text in element.xpath("./div[@class='txt-box']/h3//text()")])
            organization = "".join(element.xpath("./div[@class='txt-box']/div[@class='s-p']/span[@class='all-time-y2']/text()"))
            timestamp = "".join(element.xpath("./div[@class='txt-box']/div[@class='s-p']/span[@class='s2']//text()")).strip().replace("/n", "")
            publish_time = time_convert(timestamp[28:-3]) if timestamp else ""
            md5 = compute_md5(query, title, organization, publish_time[:10])
            if md5 in hashing_set:
                filter_num += 1
                continue
            sougou_links.append(link)
        logger.info(f"搜索关键词 '{query}'，过滤掉 {filter_num} 条重复数据")

        weixin_links = []
        for url in sougou_links:
            try:
                link = sougou2weixin(url, cookies)
                weixin_links.append(link)
            except Exception as e:
                continue
        return weixin_links


    def compute_md5(*args) -> str:
        """拼接字段并生成 MD5"""
        raw = '|'.join(arg.strip() if arg else '' for arg in args)
        return hashlib.md5(raw.encode('utf-8')).hexdigest()


    def time_convert(timestamp_str):
        timestamp = int(timestamp_str)
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
