# service/websearch/sougou_weixin.py

import hashlib
import re
import asyncio

from typing import List, Dict
from datetime import datetime
from lxml import html

from service.websearch.base import BaseSearchEngine
from models.search import SearchSougouWeixinResult
from utils.logger import get_logger
logger = get_logger(__name__)


class SougouWeixinSearchEngine(BaseSearchEngine):
    """
    搜狗微信搜索引擎实现类。
    """

    headers_search = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Referer': 'https://weixin.sogou.com',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0',
        'sec-ch-ua': '"Chromium";v="136", "Microsoft Edge";v="136", "Not.A/Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    headers_transfer = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0',
        'sec-ch-ua': '"Chromium";v="136", "Microsoft Edge";v="136", "Not.A/Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    headers_weixin = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'priority': 'u=0, i',
        'sec-ch-ua': '"Chromium";v="136", "Microsoft Edge";v="136", "Not.A/Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0',
    }

    async def asearch(self, query: str, page: int = 1, hashing_set: set[str] = set()) -> List[SearchSougouWeixinResult]:
        """
        实现百度搜索的核心逻辑。
        这里只是示例结构，暂不执行实际请求。
        """
        logger.info(f"Performing SougouWeixin search for query: {query}")

        try:
            links = await self._search(query, 1, hashing_set)
        except Exception as e:
            logger.error(f"{query} 搜索失败")
            return []

        tasks = [self.get_detail(link) for link in links]
        datas_raw = await asyncio.gather(*tasks)
        datas = [data for data in datas_raw if data is not None]

        logger.info(f"{query} 搜索完成，共获取新闻 {len(datas)} 条")
        return datas


    async def _search(self, query, page, hashing_set):
        params = {
            "type": 2,
            "s_from": "input",
            "query": f'{query}',
            "ie": "utf8",
            "page": page
        }

        try:
            response = await self.fetch('https://weixin.sogou.com/weixin', headers=self.headers_search, params=params)
        except Exception as e:
            logger.error(f"{query} 搜索失败，错误信息：{e}")
            return []

        cookies = dict(response.cookies)
        tree = html.fromstring(response.text)

        filter_num = 0
        sougou_links = []
        for element in tree.xpath("//ul[@class='news-list']/li"):
            link = "https://weixin.sogou.com"+element.xpath("./div[@class='txt-box']/h3/a/@href")[0]
            title = "".join([text.replace("\n", "").strip() for text in element.xpath("./div[@class='txt-box']/h3//text()")])
            organization = "".join(element.xpath("./div[@class='txt-box']/div[@class='s-p']/span[@class='all-time-y2']/text()"))
            timestamp = "".join(element.xpath("./div[@class='txt-box']/div[@class='s-p']/span[@class='s2']//text()")).strip().replace("/n", "")
            publish_time = self.time_convert(timestamp[28:-3]) if timestamp else ""
            md5 = self.compute_md5(query, title, organization, publish_time[:10])
            if md5 in hashing_set:
                filter_num += 1
                continue
            sougou_links.append(link)
        logger.info(f"搜索关键词 '{query}'，过滤掉 {filter_num} 条重复数据")

        weixin_transfer_tasks = [self.sougou2weixin(url, cookies) for url in sougou_links]
        weixin_links_raw = await asyncio.gather(*weixin_transfer_tasks)
        weixin_links = [link for link in weixin_links_raw if link is not None]
        return weixin_links


    async def sougou2weixin(self, url, cookies):
        try:
            response = await self.fetch(url, headers=self.headers_search, cookies=cookies)
        except Exception as e:
            logger.error(f"获取搜狗公众号链接失败: {e}")
            return None

        result = re.findall(r"url \+= '([^']*)';", response.text)
        concat_url = ''.join(result)
        return concat_url


    async def get_detail(self, url):
        try:
            response = await self.fetch(url, headers=self.headers_search)
            if "此账号已被屏蔽" in response.text or "该公众号已迁移" in response.text or "该内容已被发布者删除" in response.text:
                return None
            tree = html.fromstring(response.text)

            _title = tree.xpath('//*[@id="activity-name"]/text()')
            title = _title[0].strip().replace("\n", "") if _title else ""
            if title == "":
                return None

            _organization = tree.xpath('//*[@id="js_name"]/text()')
            organization = _organization[0].strip().replace("\n", "") if _organization else ""

            script_text = ''.join(tree.xpath('//script/text()'))
            _publish = re.search(r"var createTime = '([^']*)';", script_text)
            publish = _publish.group(1) if _publish else ""

            _location = re.search(r"provinceName: '([^']*)',", script_text)
            location = _location.group(1) if _location else ""

            _content = tree.xpath('//*[@id="js_content"]//text()')
            content = '\n'.join([line.strip().replace("\n", "") for line in _content if line.strip().replace("\n", "") != ""])

            return {
                "title": title,
                "organization": organization,
                "publish_time": publish,
                "location": location,
                "content": content,
                "md5": self.compute_md5(title, organization, publish[:10])
            }
        except Exception as e:
            None


    def compute_md5(self, *args) -> str:
        """拼接字段并生成 MD5"""
        raw = '|'.join(arg.strip() if arg else '' for arg in args)
        return hashlib.md5(raw.encode('utf-8')).hexdigest()


    def time_convert(self, timestamp_str):
        timestamp = int(timestamp_str)
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
