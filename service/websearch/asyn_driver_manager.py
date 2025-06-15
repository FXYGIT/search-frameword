import time
import logging
import asyncio
import threading
from typing import Optional, List, Callable, AsyncIterator
from contextlib import asynccontextmanager
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

class AsyncSeleniumManager:
    """
    异步管理Selenium WebDriver实例的池，提供获取和释放驱动的功能
    """
    
    def __init__(self, 
                 max_drivers: int = 2,
                 implicit_wait: int = 10,
                 page_load_timeout: int = 30,
                 headless: bool = False,
                 driver_init_callback: Optional[Callable] = None):
        """
        初始化AsyncSeleniumManager
        
        Args:
            max_drivers: 最大WebDriver实例数量
            implicit_wait: 隐式等待时间(秒)
            page_load_timeout: 页面加载超时时间(秒)
            headless: 是否使用无头模式
            driver_init_callback: WebDriver初始化后的回调函数
        """
        self.max_drivers = max_drivers
        self.implicit_wait = implicit_wait
        self.page_load_timeout = page_load_timeout
        self.headless = headless
        self.driver_init_callback = driver_init_callback
        
        # 初始化异步WebDriver队列
        self.drivers_queue = asyncio.Queue(maxsize=max_drivers)
        
        # 跟踪所有创建的driver（包括正在使用的）
        self.all_drivers = []
        
        # 初始化锁，用于线程安全操作
        self._lock = asyncio.Lock()
        
        # 初始化日志
        self.logger = logging.getLogger(__name__)
        
        # 初始化标志
        self._initialized = False
        
    async def initialize(self):
        """异步初始化WebDriver池"""
        if self._initialized:
            return
            
        async with self._lock:
            if not self._initialized:
                # 使用线程池创建WebDriver实例（因为WebDriver本身不是异步的）
                loop = asyncio.get_event_loop()
                
                # 创建所有驱动实例
                for _ in range(self.max_drivers):
                    # 在线程池中创建WebDriver
                    driver = await loop.run_in_executor(None, self._create_driver)
                    await self.drivers_queue.put(driver)
                    self.all_drivers.append(driver)
                
                self._initialized = True
                self.logger.info(f"已初始化WebDriver池，共{self.max_drivers}个实例")
            
    def _create_driver(self) -> webdriver.Chrome:
        """创建新的WebDriver实例 (同步方法，在线程池中执行)"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # 添加常用选项
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-popup-blocking")
        
        # 创建WebDriver实例
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 设置超时
        driver.implicitly_wait(self.implicit_wait)
        driver.set_page_load_timeout(self.page_load_timeout)
        
        # 如果有初始化回调，执行它
        if self.driver_init_callback:
            self.driver_init_callback(driver)
            
        self.logger.info("创建了新的WebDriver实例")
        return driver
    
    async def get_driver(self, timeout: float = 30.0) -> webdriver.Chrome:
        """
        从池中异步获取一个WebDriver实例
        
        Args:
            timeout: 获取WebDriver的超时时间(秒)
            
        Returns:
            WebDriver实例
            
        Raises:
            asyncio.TimeoutError: 如果超时仍无法获取WebDriver
        """
        # 确保池已初始化
        if not self._initialized:
            await self.initialize()
            
        try:
            self.logger.debug("尝试获取WebDriver...")
            # 使用asyncio的超时机制
            driver = await asyncio.wait_for(self.drivers_queue.get(), timeout)
            self.logger.debug("成功获取WebDriver")
            return driver
        except asyncio.TimeoutError:
            self.logger.error(f"获取WebDriver超时，当前池大小: {self.drivers_queue.qsize()}/{self.max_drivers}")
            raise asyncio.TimeoutError("无法获取WebDriver，所有实例都在使用中")
    
    async def release_driver(self, driver: webdriver.Chrome) -> None:
        """
        将WebDriver实例异步归还到池中
        
        Args:
            driver: 要归还的WebDriver实例
        """
        if driver in self.all_drivers:
            try:
                # 在线程池中执行WebDriver操作
                loop = asyncio.get_event_loop()

                # 确保切回第一个标签页
                await loop.run_in_executor(None, lambda: driver.switch_to.window(driver.window_handles[0]))
                # 清除标签页只剩一页
                await loop.run_in_executor(None, lambda: self._close_extra_tabs(driver))
                # 清除cookies并返回到空白页
                await loop.run_in_executor(None, lambda: driver.delete_all_cookies())
                await loop.run_in_executor(None, lambda: driver.get("about:blank"))
                
                await self.drivers_queue.put(driver)
                self.logger.debug("WebDriver已归还到池中")
            except Exception as e:
                self.logger.error(f"归还WebDriver时出错: {str(e)}")
                # 如果归还出错，创建新的替代
                await self._replace_driver(driver)
        else:
            self.logger.warning("尝试归还未知的WebDriver实例")

    @staticmethod
    def _close_extra_tabs(driver: webdriver.Chrome):
        handles = driver.window_handles
        main_handle = handles[0]
        for handle in handles[1:]:
            driver.switch_to.window(handle)
            driver.close()
        driver.switch_to.window(main_handle)
    async def _replace_driver(self, old_driver: webdriver.Chrome) -> None:
        """异步替换损坏的WebDriver实例"""
        async with self._lock:
            try:
                if old_driver in self.all_drivers:
                    self.all_drivers.remove(old_driver)
                
                # 在线程池中关闭旧驱动
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, lambda: self._safely_quit_driver(old_driver))
                
                # 创建新的WebDriver并添加到池中
                new_driver = await loop.run_in_executor(None, self._create_driver)
                await self.drivers_queue.put(new_driver)
                self.all_drivers.append(new_driver)
                self.logger.info("已替换损坏的WebDriver实例")
            except Exception as e:
                self.logger.error(f"替换WebDriver时出错: {str(e)}")
    
    def _safely_quit_driver(self, driver):
        """安全关闭驱动程序 (同步方法，在线程池中执行)"""
        try:
            driver.quit()
        except:
            pass
    
    @asynccontextmanager
    async def driver_context(self, timeout: float = 30.0) -> AsyncIterator[webdriver.Chrome]:
        """
        WebDriver的异步上下文管理器，使用完自动归还
        
        Args:
            timeout: 获取WebDriver的超时时间(秒)
            
        Yields:
            WebDriver实例
        """
        driver = await self.get_driver(timeout=timeout)
        try:
            yield driver
        finally:
            await self.release_driver(driver)
    
    async def close_all(self) -> None:
        """异步关闭所有WebDriver实例并清空池"""
        async with self._lock:
            # 清空队列
            while not self.drivers_queue.empty():
                try:
                    driver = self.drivers_queue.get_nowait()
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, lambda: self._safely_quit_driver(driver))
                except asyncio.QueueEmpty:
                    break
            
            # 确保所有driver都被关闭
            loop = asyncio.get_event_loop()
            for driver in self.all_drivers:
                await loop.run_in_executor(None, lambda: self._safely_quit_driver(driver))
            
            self.all_drivers.clear()
            self.logger.info("所有WebDriver实例已关闭")

manager = AsyncSeleniumManager(max_drivers=2)

async def init_driver_pool():
    await manager.initialize()

async def shutdown_driver_pool():
    await manager.close_all()