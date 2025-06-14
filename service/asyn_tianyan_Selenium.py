import time
import logging
from typing import Dict, Any, List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from service.websearch.selenium_manager import SeleniumManager
class AsynTianyanChaSpider:
    def __init__(self, selenium_manager: SeleniumManager):
        """
        初始化天眼查爬虫
        
        Args:
            selenium_manager: WebDriver管理器实例
        """
        self.selenium_manager = selenium_manager
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://www.tianyancha.com"

    def _extract_company_info(self, driver: webdriver.Chrome) -> Dict[str, Any]:
            """
            从公司详情页提取信息
            
            Args:
                driver: WebDriver实例
                
            Returns:
                公司信息字典
            """
            company_info = {}
            
            try:
                # 提取公司名称
                company_info['company_name'] = driver.find_element(By.XPATH, "//h1//span[contains(@class, 'name')]").text
            except:
                company_info['company_name'] = ""
                
            try:
                # 公司状态
                company_info['company_status'] = driver.find_element(By.XPATH, "(//div[contains(@class, 'company-tag')])[1]").text
            except:
                company_info['company_status'] = ""
                
            try:
                # 统一社会信用代码
                company_info['unified_code'] = driver.find_element(By.XPATH, "//span[contains(@class, 'credit-code')]//span").text
            except:
                company_info['unified_code'] = ""
                
            try:
                # 公司标签
                company_info['company_type'] = [element.text.strip()
        for element in driver.find_elements(By.XPATH, "//div[contains(@class, 'index_tag')]/div[contains(@class, 'index_company-tag')]")
        if element.text.strip()]
            except:
                company_info['company_type'] = []
                
            # 可以继续添加更多需要提取的信息
            
            return company_info
        
    def get_company_details(self, company_id: str) -> Optional[Dict[str, Any]]:
        """
        通过公司ID直接获取公司详情
        
        Args:
            company_id: 天眼查公司ID
            
        Returns:
            公司详情字典，失败返回None
        """
        with self.selenium_manager.driver_context() as driver:
            try:
                # 直接访问公司详情页
                url = f"{self.base_url}/company/{company_id}"
                driver.get(url)
                
                # 检查是否需要登录
                if not self._login_if_needed(driver):
                    self.logger.error("登录失败，无法获取公司详情")
                    return None
                
                # 等待公司详情页加载
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'company-header-main')]"))
                )
                
                # 提取公司信息
                company_info = self._extract_company_info(driver)
                
                return company_info
                
            except Exception as e:
                self.logger.error(f"获取公司详情时出错: {str(e)}")
                return None

    
    
    async def asearch(self, query: str, selenium_manager: Optional[SeleniumManager] = None) -> List[Dict[str, Any]]:
        """
        异步搜索公司或其他信息

        Args:
            query: 搜索关键词
            selenium_manager: 可选的SeleniumManager实例，如果不提供则使用self.selenium_manager

        Returns:
            搜索结果列表，每个结果是一个字典
        """
        import asyncio
    
        # 使用提供的selenium_manager或默认的实例
        manager = selenium_manager or self.selenium_manager
        
        try:
            # 如果manager.driver_context()是异步上下文管理器，需要使用async with
            # 而不是在线程池中运行search_company
            
            # 方法1：如果AsyncSeleniumManager提供异步上下文管理器
            async with manager.driver_context() as driver:
                # 在这里直接执行所需的操作
                # 注意：所有selenium操作都需要包装在run_in_executor中
                loop = asyncio.get_running_loop()
                
                # 访问天眼查首页
                await loop.run_in_executor(None, lambda: driver.get(self.base_url))
                
                # 检查是否需要登录
                login_result = await loop.run_in_executor(None, lambda: self._login_if_needed(driver))
                if not login_result:
                    self.logger.error("登录失败，无法搜索公司")
                    return []
                
                # 搜索公司
                # 注意：每个selenium操作都需要使用run_in_executor
                
                # 在搜索框中输入公司名称
                await loop.run_in_executor(None, lambda d=driver, q=query: self._search_input(d, q))
                
                # 提取结果
                company_info = await loop.run_in_executor(None, lambda d=driver: self._extract_company_info(d))
                
                if company_info:
                    # 转换为API期望的格式
                    return [{
                        "title": company_info.get("company_name", "未知公司"),
                        "url": f"https://www.tianyancha.com/search?key={query}",
                        "content": self._format_company_info(company_info),
                        "source": "tianyancha",
                        "metadata": company_info
                    }]
                else:
                    self.logger.warning(f"搜索公司 {query} 失败")
                    return []
        except Exception as e:
            self.logger.error(f"异步搜索过程中出错: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return []
    
    def _format_company_info(self, company_info: Dict[str, Any]) -> str:
        """将公司信息格式化为可读文本"""
        info_text = []
        
        if company_info.get('company_name'):
            info_text.append(f"公司名称: {company_info['company_name']}")
            
        if company_info.get('company_status'):
            info_text.append(f"公司状态: {company_info['company_status']}")
            
        if company_info.get('unified_code'):
            info_text.append(f"统一社会信用代码: {company_info['unified_code']}")
            
        if company_info.get('company_type'):
            info_text.append(f"公司类型: {', '.join(company_info['company_type'])}")
        
        # 可以添加更多信息字段
        
        return "\n".join(info_text)
    def _search_input(self, driver, query):
        """处理搜索输入（提取为辅助方法，便于在异步函数中调用）"""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import time
        
        # 在搜索框中输入公司名称
        search_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "/html[1]/body[1]/div[1]/div[1]/div[1]/div[1]/div[3]/div[2]/div[1]/div[1]/input[1]"))
        )
        search_input.clear()
        search_input.send_keys(query)
        
        # 点击搜索按钮
        search_button = driver.find_element(By.XPATH, "(//button[span[text()='天眼一下']])[2]")
        search_button.click()
        
        # 等待搜索结果加载
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@id= 'page-container']"))
        )
        
        # 点击第一个搜索结果
        first_result = driver.find_element(By.XPATH, "//div[contains(@class, 'list-content')]//a[contains(., '{}')]".format(query))
        first_result.click()
        
        # 切换到新打开的标签页
        driver.switch_to.window(driver.window_handles[-1])
        
        # 等待公司详情页加载
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'company-header-main')]"))
        )
        
        return True