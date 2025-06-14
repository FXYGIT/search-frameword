import time
import logging
import queue
import threading
from typing import Optional, List, Callable, AsyncIterator
from contextlib import contextmanager
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from contextlib import asynccontextmanager
import asyncio




class SeleniumManager:
    """
    管理Selenium WebDriver实例的池，提供获取和释放驱动的功能
    """
    
    def __init__(self, 
                 max_drivers: int = 3, 
                 implicit_wait: int = 10,
                 page_load_timeout: int = 30,
                 headless: bool = False,
                 driver_init_callback: Optional[Callable] = None):
        """
        初始化SeleniumManager
        
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
        
        # 初始化WebDriver队列
        self.drivers_queue = queue.Queue(maxsize=max_drivers)
        
        # 跟踪所有创建的driver（包括正在使用的）
        self.all_drivers = []
        
        # 初始化锁，用于线程安全操作
        self._lock = threading.RLock()
        
        # 初始化日志
        self.logger = logging.getLogger(__name__)
        
        # 初始化WebDriver池
        self._initialize_drivers()
    
    def _initialize_drivers(self) -> None:
        """初始化WebDriver池"""
        for _ in range(self.max_drivers):
            driver = self._create_driver()
            self.drivers_queue.put(driver)
            self.all_drivers.append(driver)
            
    def _create_driver(self) -> webdriver.Chrome:
        """创建新的WebDriver实例"""
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
    
    def get_driver(self, timeout: int = 30) -> webdriver.Chrome:
        """
        从池中获取一个WebDriver实例
        
        Args:
            timeout: 获取WebDriver的超时时间(秒)
            
        Returns:
            WebDriver实例
            
        Raises:
            TimeoutError: 如果超时仍无法获取WebDriver
        """
        try:
            self.logger.debug("尝试获取WebDriver...")
            driver = self.drivers_queue.get(timeout=timeout)
            self.logger.debug("成功获取WebDriver")
            return driver
        except queue.Empty:
            self.logger.error(f"获取WebDriver超时，当前池大小: {self.drivers_queue.qsize()}/{self.max_drivers}")
            raise TimeoutError("无法获取WebDriver，所有实例都在使用中")
    
    def release_driver(self, driver: webdriver.Chrome) -> None:
        """
        将WebDriver实例归还到池中
        
        Args:
            driver: 要归还的WebDriver实例
        """
        if driver in self.all_drivers:
            try:
                # 清除cookies并返回到空白页
                driver.delete_all_cookies()
                driver.get("about:blank")
                self.drivers_queue.put(driver)
                self.logger.debug("WebDriver已归还到池中")
            except Exception as e:
                self.logger.error(f"归还WebDriver时出错: {str(e)}")
                # 如果归还出错，创建新的替代
                self._replace_driver(driver)
        else:
            self.logger.warning("尝试归还未知的WebDriver实例")
    
    def _replace_driver(self, old_driver: webdriver.Chrome) -> None:
        """替换损坏的WebDriver实例"""
        with self._lock:
            try:
                if old_driver in self.all_drivers:
                    self.all_drivers.remove(old_driver)
                
                try:
                    old_driver.quit()
                except:
                    pass
                
                # 创建新的WebDriver并添加到池中
                new_driver = self._create_driver()
                self.drivers_queue.put(new_driver)
                self.all_drivers.append(new_driver)
                self.logger.info("已替换损坏的WebDriver实例")
            except Exception as e:
                self.logger.error(f"替换WebDriver时出错: {str(e)}")
    
    @contextmanager
    def driver_context(self, timeout: int = 30):
        """
        WebDriver的上下文管理器，使用完自动归还
        
        Args:
            timeout: 获取WebDriver的超时时间(秒)
            
        Yields:
            WebDriver实例
        """
        driver = self.get_driver(timeout=timeout)
        try:
            yield driver
        finally:
            self.release_driver(driver)
    
    def close_all(self) -> None:
        """关闭所有WebDriver实例并清空池"""
        with self._lock:
            # 先清空队列
            while not self.drivers_queue.empty():
                try:
                    driver = self.drivers_queue.get_nowait()
                    try:
                        driver.quit()
                    except:
                        pass
                except queue.Empty:
                    break
            
            # 确保所有driver都被关闭
            for driver in self.all_drivers:
                try:
                    driver.quit()
                except:
                    pass
            
            self.all_drivers.clear()
            self.logger.info("所有WebDriver实例已关闭")