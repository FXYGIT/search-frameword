import time
import logging
from typing import Dict, Any, List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import asyncio
from service.websearch.driver_manager import SeleniumManager

class TianyanChaSpider:
    """天眼查爬虫，使用SeleniumManager管理WebDriver"""
    
    def __init__(self, selenium_manager: SeleniumManager):
        """
        初始化天眼查爬虫
        
        Args:
            selenium_manager: WebDriver管理器实例
        """
        self.selenium_manager = selenium_manager
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://www.tianyancha.com"
    
    def _login_if_needed(self, driver: webdriver.Chrome) -> bool:
        """
        检查是否需要登录，如果需要则尝试登录
        
        Args:
            driver: WebDriver实例
            
        Returns:
            是否登录成功
        """
        # 检查是否已登录
        try:
            # 检查页面上是否有登录按钮或其他登录状态元素
            # 这里需要根据实际网站结构调整
            # login_btn = driver.find_elements(By.XPATH, "//div[contains(@class, 'login')]")
            # if not login_btn:
            #     # 没有登录按钮，可能已登录
            #     return True
                
            # TODO: 实现登录逻辑
            driver.get(self.base_url)
            time.sleep(1)
            try:
                    driver.add_cookie({'name': 'auth_token',
                                       'value': 'eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiIxNTk3MTAxOTQ5MCIsImlhdCI6MTc0OTczNDM4OCwiZXhwIjoxNzUyMzI2Mzg4fQ.LKUQtak6mJDnxr2je9tbptUw26XzMVLafdmPRGPNJwKlzcEfy2lu7iG5WInzcnZVt0PY4l1rXAVfVyq0A4nuFA'})
            except Exception as e:
                self.logger.warning(f"添加cookie失败: {str(e)}")
            driver.refresh()
            time.sleep(2)
            return True
        except Exception as e:
            self.logger.error(f"登录过程出错: {str(e)}")
            return False
    
    def search_company(self, company_name: str) -> Optional[Dict[str, Any]]:
        """
        搜索公司信息
        
        Args:
            company_name: 公司名称
            
        Returns:
            公司信息字典，搜索失败返回None
        """
        with self.selenium_manager.driver_context() as driver:
            try:
                # 访问天眼查首页
                driver.get(self.base_url)
                try:
                    self._login_if_needed(driver)
                except Exception as e:
                    self.logger.error(f"登录失败: {str(e)}")
                    return None
                
                # 在搜索框中输入公司名称
                search_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "/html[1]/body[1]/div[1]/div[1]/div[1]/div[1]/div[3]/div[2]/div[1]/div[1]/input[1]"))
                )
                search_input.clear()
                search_input.send_keys(company_name)
                
                # 点击搜索按钮
                search_button = driver.find_element(By.XPATH, "(//button[span[text()='天眼一下']])[2]")
                search_button.click()
                
                
                # 等待搜索结果加载
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@id= 'page-container']"))
                )
                
                # 点击第一个搜索结果
                first_result = driver.find_element(By.XPATH, "//div[contains(@class, 'list-content')]//a[contains(., '{}')]".format(company_name))
                first_result.click()
                
                # 切换到新打开的标签页
                driver.switch_to.window(driver.window_handles[-1])
                
                # 等待公司详情页加载
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'company-header-main')]"))
                )
                
                # 提取公司信息
                company_info = self._extract_company_info(driver)
                
                return company_info
                
            except TimeoutException as e:
                self.logger.error(f"页面加载超时: {str(e)}")
                return None
            except Exception as e:
                self.logger.error(f"搜索公司时出错: {str(e)}")
                return None
    
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

    def search(self, query: str, selenium_manager: SeleniumManager) -> List[Dict[str, Any]]:
        """
        搜索公司或其他信息

        Args:
            query: 搜索关键词
            selenium_manager: SeleniumManager实例

        Returns:
            搜索结果列表，每个结果是一个字典
        """
        try:
            # 初始化天眼查爬虫
            spider = TianyanChaSpider(selenium_manager)
            
            # 示例：搜索公司
            companies = [query]  # 可以替换为实际的公司名称列表
            
            for company_name in companies:
                print(f"正在搜索公司: {company_name}")
                result = spider.search_company(company_name)
                
                if result:
                    return [result]
                else:
                    print(f"搜索公司 {company_name} 失败")
                    return []
        except Exception as e:
            logging.error(f"搜索过程中出错: {str(e)}")
            return []
        finally:
            # 确保关闭所有WebDriver实例
            selenium_manager.close_all()
    
    



    async def asearch(self, query: str, async_manager=None) -> List[Dict[str, Any]]:
        """
        异步接口，在内部使用同步方法执行实际爬取
        
        Args:
            query: 搜索关键词
            async_manager: 可选的AsyncSeleniumManager实例
            
        Returns:
            搜索结果列表
        """
        # 使用提供的异步管理器或保存的管理器
        manager = async_manager or self.selenium_manager
        
        # 确保我们有一个异步管理器
        if not hasattr(manager, 'driver_context') or not asyncio.iscoroutinefunction(manager.get_driver):
            raise TypeError("异步搜索需要AsyncSeleniumManager实例")
            
        try:
            # 获取一个WebDriver
            driver = await manager.get_driver()
            
            try:
                # 使用获取的driver执行同步爬取逻辑
                # 将同步代码包装在run_in_executor中执行
                loop = asyncio.get_running_loop()
                
                # 执行同步的搜索逻辑，传入已获取的driver
                result = await loop.run_in_executor(
                    None, 
                    self._sync_search_with_driver, 
                    driver, 
                    query
                )
                
                if result:
                    # 转换为API所需的格式
                    return [result]

                else:
                    self.logger.warning(f"搜索公司 {query} 失败")
                    return []
                    
            finally:
                # 归还driver到池中
                self.logger.debug("开始后台释放 driver")
                asyncio.create_task(self._safe_release(driver, manager))
                
        except Exception as e:
            self.logger.error(f"异步搜索过程中出错: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return []

    async def _safe_release(self, driver, manager):
        try:
            await manager.release_driver(driver)
        except Exception as e:
            self.logger.warning(f"释放 driver 时出错: {e}")
    def _sync_search_with_driver(self, driver, query):
        """
        使用给定的driver执行同步搜索
        这是一个内部方法，由asearch调用
        """
        try:
            # 访问天眼查首页
            driver.get(self.base_url)
            
            # 登录处理
            self._login_if_needed(driver)
            
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
            
            # 提取公司信息
            return self._extract_company_info(driver)
            
        except Exception as e:
            self.logger.error(f"同步搜索过程中出错: {str(e)}")
            return None
    
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
        
        return "\n".join(info_text)