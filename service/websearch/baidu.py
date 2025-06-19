import hashlib

import asyncio
from typing import List, Dict, Optional
import httpx
import requests

from service.websearch.base import BaseSearchEngine
from models.search import SearchBaiduResult  # 建议新建通用模型
from lxml import html
from utils.logger import get_logger


logger = get_logger(__name__)


class BaiduSearchEngine(BaseSearchEngine):
    """
    百度网页搜索引擎实现类。
    """

    headers_search  = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}


    results_per_page = 10
    def __init__(self):
        self.sem = asyncio.Semaphore(20)  # 控制并发量
        self.logger = logger

    async def asearch(self, query: str, page: int = 1, hashing_set: set[str] = set()) -> List[SearchBaiduResult]:
        logger.info(f"Performing Baidu search for query: {query}")
        try:
            links = await self._search(query, page, hashing_set)
        except Exception as e:
            logger.error(f"Baidu search failed: {e}")
            return []

        tasks = [self.get_detail(link) for link in links]
        raw_results = await asyncio.gather(*tasks)
        #  过滤空 title或者 content
        results =[ result for result in raw_results  if  result is not None and result.get("title", "").strip() and result.get("content", "").strip() ]
        logger.info(f"Baidu search finished, got {len(results)} new articles")
        return results


    async def _search(self, query: str, page: int, hashing_set: set[str]) -> List[str]:
        # params = {
        #     "wd": query,
        #     "pn": (page - 1) * self.results_per_page,
        #     "ie": "utf-8",
        #     "rn": self.results_per_page,
        #     "tn": "baidu",
        # }
        params = {
            'ie': 'utf-8',
            'f': '8',
            'rsv_bp': '1',
            'rsv_idx': '1',
            'tn': 'baidu',
            'wd': f"{query}",
            'fenlei': '256',
            'rqlang': 'en',
            'rsv_enter': '1',
            'rsv_dl': 'tb',
            'rsv_sug7': '100',
            'rsv_sug2': '0',
            'rsv_btype': 'i',
        }


        try:
            response = await self.fetch('https://www.baidu.com/s', headers=self.headers_search, params=params)
        except httpx.RequestError as e:
            logger.error(f"{query} 搜索失败，错误信息：{e}")
            return []
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 302:
                if "verify" in str(response.url) or "验证码" in response.text:
                    logger.warning("百度反爬验证页被触发")
                    return None
                else:
                    redirect_url = e.response.headers.get("Location")
                    response = await self.fetch(redirect_url, headers=self.headers_search)

        # cookies = dict(response.cookies)
        tree = html.fromstring(response.text)
        filter_num = 0
        baidu_links = []

        elements = tree.xpath("//div[@class='result c-container xpath-log new-pmd']")
        for element in elements:
            hrefs = element.xpath(".//h3/a/@href")[0]
            if not hrefs:
                continue

            title = "".join(
                [text.replace("\n", "").strip() for text in element.xpath(".//span[@class='tts-b-hl']//text()")])
            md5 = self.compute_md5(query, title)

            if md5 in hashing_set:
                filter_num += 1
                continue

            baidu_links.append(hrefs)

        # 单独处理百度百科
        # element_baike = tree.xpath("//div[@class='result-op c-container xpath-log new-pmd']")
        # if element_baike:
        #     hrefs = element_baike.xpath(".//h3/a/@href")[0]
        #     title = "".join(
        #         [text.replace("\n", "").strip() for text in element_baike.xpath(".//span[@class='tts-b-hl']//text()")])
        #     md5 = self.compute_md5(query, title)
        #     if md5 in hashing_set:
        #         filter_num += 1
        #     baidu_links.append(hrefs)

        logger.info(f"关键词 '{query}'，过滤 {filter_num} 条重复，待解析 {len(baidu_links)} 条链接")
        baidu_transfer_tasks = [self.resolve_real_url(url) for url in baidu_links]
        baidu_links_raw = await asyncio.gather(*baidu_transfer_tasks)
        baidu_links = [link for link in baidu_links_raw if link is not None]
        return baidu_links


    async def resolve_real_url(self, url) -> str:
        try:
            res = requests.get(url, allow_redirects=False)
            if res.status_code in [301, 302]:
                redirect_url = res.headers.get('Location')
                print(redirect_url)
                return redirect_url
        except Exception as e:
            logger.warning(f"重定向失败 {url}")
            return url


    async def get_detail(self, url):
        try:
            try:
                response = await self.fetch(url, headers=self.headers_search)
            except (httpx.RequestError) as e:
                logger.error(f"{url} httpx.RequestError：{e}")
                return None
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 302:
                    if "verify" in str(e.response.url) or "验证码" in e.response.text:
                        logger.warning("百度反爬验证页被触发")
                        return None
                    else:
                        response = await self.fetch(url, headers=self.headers_search)
            except Exception as e:
                logger.error(f"无法获取具体页面响应:{e}")

            tree = html.fromstring(response.text)

            _title = tree.xpath(
                "//title/text()")
            title = _title[0].strip().replace("\n", "") if _title else ""


            _content = tree.xpath("//p//text()")
            content = '\n'.join([line.strip().replace("\n", "") for line in _content if line.strip().replace("\n", "") != ""])
            # 如果内容为空 直接返回none

            return {
                "title": title,
                "content": content,
                "md5": self.compute_md5(title, content)
            }

        except Exception as e:
            logger.error(f"解析详情页失败，URL：{url}，错误信息：{e}")
            return None

    def compute_md5(self, *args: str) -> str:
        raw = '|'.join(arg.strip() if arg else '' for arg in args)
        return hashlib.md5(raw.encode('utf-8')).hexdigest()








