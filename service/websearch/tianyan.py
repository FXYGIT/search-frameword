# service/websearch/tianyan.py
import httpx
import hashlib
import re
import random
import time
from typing import List, Dict, Any, Optional
from urllib.parse import quote, urljoin
from lxml import html
from utils.proxy import get_proxy
from service.websearch.base import BaseSearchEngine
from models.search import SearchTianyanResult
from utils.logger import get_logger
from utils.proxy import get_proxy_sync
from utils.http_client import get_http_client
from tenacity import retry, stop_after_attempt, wait_fixed, RetryError, before_sleep_log
import requests
from urllib.parse import quote, urljoin
from utils.logger import get_logger
logger = get_logger(__name__)


class TianyanSearchEngine(BaseSearchEngine):

    headers_search = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Accept-Language': 'zh-CN,zh;q=0.9,zh-TW;q=0.8',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Host': 'www.tianyancha.com',
    'Referer': rf'https://www.tianyancha.com/nsearch?key=%E5%B0%8F%E7%B1%B3',
    'Sec-Ch-Ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
    }
    
    headers_detail = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Accept-Language': 'zh-CN,zh;q=0.9,zh-TW;q=0.8',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Host': 'www.tianyancha.com',
    'Referer': rf'https://www.tianyancha.com/nsearch?key=%E5%B0%8F%E7%B1%B3',
    'Sec-Ch-Ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
    }

    # 天眼查需要更新的Cookie
    cookies = {
        "auth_token": "eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiIxNTk3MTAxOTQ5MCIsImlhdCI6MTc0OTczNDM4OCwiZXhwIjoxNzUyMzI2Mzg4fQ.LKUQtak6mJDnxr2je9tbptUw26XzMVLafdmPRGPNJwKlzcEfy2lu7iG5WInzcnZVt0PY4l1rXAVfVyq0A4nuFA",  
    }  # 初始化为空字典，可以在运行时设置
    
    base_url = 'https://www.tianyancha.com'
    search_url = 'https://www.tianyancha.com/nsearch'

    async def asearch(self, query: str, page: int = 1, hashing_set: set = None) -> List[Dict[str, Any]]:
        """异步接口方法，实际调用同步的 search 方法
        
        这个方法提供与 BaseSearchEngine 接口兼容的异步入口点，
        但内部实现仍然是同步的。
        """
        return self.search(query, page, hashing_set)
    def search(self, query: str, page: int = 1, hashing_set: set = None) -> List[Dict[str, Any]]:
        """同步方式搜索企业信息"""
        if hashing_set is None:
            hashing_set = set()
            
        logger.info(f"开始天眼查搜索: {query}")

        try:
            company_items = self._search(query, page, hashing_set)
            
            if company_items:
                details = []
                for item in company_items:
                    detail = self.get_company_detail(item)
                    if detail is not None:
                        details.append(detail)
                
                logger.info(f"搜索完成，获取到 {len(details)} 家公司信息")
                return details
            else:
                logger.warning(f"未找到与 '{query}' 相关的公司")
                return []
            
        except Exception as e:
            logger.error(f"天眼查搜索失败: {str(e)}")
            return []

    def _search(self, query: str, page: int, hashing_set: set) -> List[Dict[str, Any]]:
        """搜索公司列表"""
        time.sleep(random.uniform(3, 7))
        params = {
            'key': query,
            # 'page': page
        }
        
        try:
            response = self.fetch_with_redirect_requests(
                self.search_url,
                headers=self.headers_search,
                params=params,
            )

            tree = html.fromstring(response.text)

            company_items = []
            filter_num = 0
            
            for element in tree.xpath("/html[1]/body[1]/div[1]/div[2]/div[1]/div[2]/div[1]/div[2]/div[2]/div/div/div[2]"):
                try:
                    name_element = element.xpath(".//div[@class = 'index_name__qEdWi']")[0]
                    company_name = name_element.text_content().strip()
                    company_link = element.xpath(".//div[@class = 'index_name__qEdWi']/a/@href")[0]
                    
                    legal_person_element = element.xpath(".//div[contains(text(), '法定代表人')]/span//a/span/text()")
                    legal_person = legal_person_element[0].text_content().strip() if legal_person_element else None
                    
                    date_element = element.xpath(".//div[contains(text(), '成立日期')]/span/text()")
                    establishment_date = date_element[0].text_content().strip() if date_element else None
                    
                    md5 = self.compute_md5(company_name, legal_person or '', establishment_date or '', company_link)
                    
                    if md5 in hashing_set:
                        filter_num += 1
                        continue
                    
                    company_items.append({
                        "company_name": company_name,
                        "legal_person": legal_person,
                        "establishment_date": establishment_date,
                        "company_link": company_link,
                        "md5": md5
                    })
                    
                except Exception as e:
                    logger.error(f"解析公司条目时出错: {str(e)}")
                    continue
            
            logger.info(f"搜索关键词 '{query}'，找到 {len(company_items)} 家公司，过滤掉 {filter_num} 条重复数据")
            return company_items
            
        except Exception as e:
            logger.error(f"搜索过程中出错: {str(e)}")
            return []

    def get_company_detail(self, company_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """获取公司详细信息"""
        detail_headers = self.headers_detail.copy()
        detail_headers['Referer'] = self.search_url + f"?key={quote(company_item['company_name'])}"
        time.sleep(random.uniform(4, 8))
        
        try:
            time.sleep(random.uniform(1, 3))

            response = self.fetch_with_redirect(
                company_item["company_link"],
                headers=detail_headers,
                cookies=self.cookies
            )
            
            if "访问已经受限" in response.text or "验证码" in response.text:
                logger.warning(f"访问受限或需要验证码: {company_item['company_name']}")
                return None

            tree = html.fromstring(response.text)

            try:
                company_type_element = tree.xpath("/html[1]/body[1]/div[1]/div[1]/div[3]/div[1]/div[1]/div[1]/div[2]/div[1]/div[1]/div[2]/div[2]")
                company_type = company_type_element[0].text_content().strip() if company_type_element else None

                company_status_element = tree.xpath("/html[1]/body[1]/div[1]/div[1]/div[3]/div[1]/div[1]/div[1]/div[2]/div[1]/div[1]/div[2]/div[1]/div[1]/h1[1]/div[1]/div[1]")
                company_status = company_status_element[0].text_content().strip() if company_status_element else None
                
                company_basic_info_element = tree.xpath("//div[@class='index_detail__JSmQM']")
                company_basic_info = company_basic_info_element[0].text_content().strip() if company_basic_info_element else None

                company_item.update({
                    "company_basic_info": company_basic_info,
                    "company_type": company_type,
                    "company_status": company_status
                })
                
                return company_item
                
            except Exception as e:
                logger.error(f"解析公司详情时出错: {str(e)}")
                return company_item
                
        except Exception as e:
            logger.error(f"获取公司详情失败: {str(e)}")
            return None

    def compute_md5(self, *args) -> str:
        """拼接字段并生成 MD5，用于去重"""
        raw = '|'.join(arg.strip() if arg else '' for arg in args)
        return hashlib.md5(raw.encode('utf-8')).hexdigest()

    def fetch_with_redirect(self, url, max_retries=5, handle_redirects=True, **kwargs):
        """发送HTTP请求并处理重定向"""
        attempt = 0
        last_exception = None
        if 'params' in kwargs:
            params = kwargs.pop('params')
        while attempt < max_retries:
            client = None
            
            try:
                attempt += 1
                try: # 导入同步版本的函数
                    proxy = get_proxy_sync()  # 使用同步版本
                    logger.debug(f"获取代理成功: {proxy}")
                except Exception as e:
                    logger.warning(f"获取代理失败: {str(e)}")
                    proxy = None
                    
                try:
                    # 创建HTTP客户端
                    client = self.get_http_client()
                    logger.debug(f"尝试 #{attempt}，使用代理: {proxy}")
                except Exception as e:
                    logger.error(f"创建HTTP客户端失败: {str(e)}")
                    time.sleep(2)
                    continue
                
                # 如果不需要处理重定向，直接禁用它
                if not handle_redirects:
                    kwargs['follow_redirects'] = False

                if params:
                    # 使用字符串拼接构建URL
                    query_string = '&'.join([f"{key}={quote(str(value))}" for key, value in params.items()])
                    full_url = f"{url}{'?' if '?' not in url else '&'}{query_string}"
                    logger.debug(f"请求完整URL: {full_url}")
                    response = client.get(full_url, timeout=15, **kwargs)
                else:
                    logger.warning(f"没有携带参数，使用默认参数请求: {url}")
                    response = client.get(url, timeout=15, **kwargs)

                # 检查是否有重定向需要处理
                if handle_redirects and 300 <= response.status_code < 400:
                    redirect_url = response.headers.get('location')
                    if redirect_url:
                        if not redirect_url.startswith('http'):
                            # 处理相对URL
                            redirect_url = urljoin(url, redirect_url)
                        
                        logger.info(f"处理重定向: {url} -> {redirect_url}")
                        
                        # 检查是否重定向到登录页面
                        if 'login' in redirect_url.lower() or 'signin' in redirect_url.lower():
                            logger.warning(f"重定向到登录页面，跳过处理: {redirect_url}")
                            continue
                            
                        time.sleep(random.uniform(1, 2))
                        
                        # 更新headers中的Referer
                        if 'headers' in kwargs:
                            kwargs['headers'] = dict(kwargs['headers'])
                            kwargs['headers']['Referer'] = url
                        
                        # 递归调用自身处理重定向
                        return self.fetch_with_redirect(redirect_url, max_retries=max_retries-1, **kwargs)
                
                # 对于非重定向状态码，检查是否成功
                response.raise_for_status()
                return response
                
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                last_exception = e
                logger.warning(f"请求失败: {str(e)}")
                
                # 计算指数退避时间
                backoff_time = min(2 ** attempt, 30) * random.uniform(0.5, 1.5)
                logger.info(f"等待 {backoff_time:.2f} 秒后重试...")
                time.sleep(backoff_time)
            
            finally:
                if client:
                    try:
                        client.close()
                    except Exception as e:
                        logger.warning(f"关闭HTTP客户端失败: {str(e)}")
        
        # 如果所有重试都失败
        logger.error(f"达到最大重试次数 {max_retries}，请求失败: {url}")
        if last_exception:
            raise last_exception
        else:
            raise Exception(f"请求失败，原因未知: {url}")

    def get_http_client(self, proxy=None, timeout=30, verify=True, **kwargs):

        """
        创建HTTP客户端
        """
        defaults = {
            "timeout": timeout,
            "verify": verify,
            "follow_redirects": True,
        }
        
        # 合并用户提供的配置
        client_kwargs = {**defaults}
        
        # 如果提供了代理，添加到配置中 - 修正代理设置方式
        if proxy:
            transport = httpx.HTTPTransport(proxy=proxy)
            client_kwargs["transport"] = transport
        
        # 创建并返回客户端
        return httpx.Client(**client_kwargs)
    



    def fetch_with_redirect_requests(self,url, max_retries=5, handle_redirects=True, **kwargs):
        """
        使用 requests 库发送 HTTP 请求，并处理重定向
        参数:
        url: 请求的 URL
        max_retries: 最大重试次数
        handle_redirects: 是否自动处理重定向
        kwargs: 其他传递给 requests.get 的关键字参数，其中可以包含 'params'
        返回:
        response 对象
        """
        attempt = 0
        last_exception = None

        # 保存原始的 params 参数，避免在循环中被消费掉
        original_params = kwargs.pop('params', None)

        while attempt < max_retries:
            try:
                attempt += 1

                if original_params:
                    # 使用字符串拼接构建 URL 参数
                    query_string = '&'.join([f"{key}={quote(str(value))}" for key, value in original_params.items()])
                    full_url = f"{url}{'?' if '?' not in url else '&'}{query_string}"
                    logger.debug(f"请求完整URL: {full_url}")
                    response = requests.get(full_url, timeout=15, allow_redirects=handle_redirects, **kwargs)
                else:
                    logger.warning(f"没有携带参数，使用默认参数请求: {url}")
                    response = requests.get(url, timeout=15, allow_redirects=handle_redirects, **kwargs)

                # 手动处理重定向情况（当 handle_redirects=True 时，requests 会自动处理，
                # 但如果不希望自动处理全部重定向，可通过该逻辑进行定制处理）
                if handle_redirects and 300 <= response.status_code < 400:
                    redirect_url = response.headers.get('location')
                    if redirect_url:
                        if not redirect_url.startswith('http'):
                            redirect_url = urljoin(url, redirect_url)
                        logger.info(f"处理重定向: {url} -> {redirect_url}")

                        # 等待一段时间后重试
                        time.sleep(random.uniform(1, 2))
                        return self.fetch_with_redirect_requests(redirect_url, max_retries=max_retries-1,
                                                            handle_redirects=handle_redirects, **kwargs)

                response.raise_for_status()
                return response

            except requests.RequestException as e:
                last_exception = e
                logger.warning(f"请求失败: {str(e)}")
                backoff_time = min(2 ** attempt, 30) * random.uniform(0.5, 1.5)
                logger.info(f"等待 {backoff_time:.2f} 秒后重试...")
                time.sleep(backoff_time)

        # 如果达到重试次数仍然失败，抛出异常
        logger.error(f"达到最大重试次数 {max_retries}，请求失败: {url}")
        if last_exception:
            raise last_exception
        else:
            raise Exception(f"请求失败，原因未知: {url}")
        