import asyncio
import logging
from typing import Callable, Optional
from selenium import webdriver
from selenium.common.exceptions import WebDriverException

class AsyncDriverManager:
    def __init__(self, max_drivers=4, headless=True, check_interval=60, max_retries=3,
                 driver_factory: Optional[Callable[[], webdriver.Chrome]] = None):
        self.max_drivers = max_drivers
        self.headless = headless
        self.check_interval = check_interval
        self.max_retries = max_retries
        self.drivers_queue = asyncio.Queue()
        self.all_drivers = set()
        self.monitoring = True
        self.logger = logging.getLogger("AsyncDriverManager")

        # 如果提供了外部创建方法，就用；否则使用默认创建
        self.driver_factory = driver_factory or self._default_driver_factory

    async def initialize(self):
        for _ in range(self.max_drivers):
            driver = await self._create_driver_with_retry()
            if driver:
                await self.drivers_queue.put(driver)
                self.all_drivers.add(driver)
        asyncio.create_task(self._monitor_pool())

    async def get_driver(self):
        driver = await self.drivers_queue.get()
        return AsyncDriverContext(self, driver)

    async def release_driver(self, driver):
        if await self._check_driver(driver):
            await self.drivers_queue.put(driver)
        else:
            await self._replace_driver(driver)

    def _default_driver_factory(self):
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        return webdriver.Chrome(options=options)

    async def _create_driver_with_retry(self):
        for attempt in range(1, self.max_retries + 1):
            try:
                driver = self.driver_factory()
                await self.on_create(driver)
                self.logger.info(f"✅ Driver created (attempt {attempt})")
                return driver
            except Exception as e:
                self.logger.warning(f"❌ Failed to create driver (attempt {attempt}): {e}")
                await asyncio.sleep(2)
        self.logger.error("💥 Exceeded max retries for driver creation")
        return None

    async def _check_driver(self, driver):
        try:
            _ = driver.title
            return True
        except WebDriverException:
            return False

    async def _replace_driver(self, bad_driver):
        await self.on_destroy(bad_driver)
        try:
            bad_driver.quit()
        except:
            pass
        self.all_drivers.discard(bad_driver)
        new_driver = await self._create_driver_with_retry()
        if new_driver:
            await self.drivers_queue.put(new_driver)
            self.all_drivers.add(new_driver)

    async def _monitor_pool(self):
        while self.monitoring:
            await asyncio.sleep(self.check_interval)
            self.logger.info("🔍 Checking driver pool health...")
            to_replace = []
            for driver in list(self.all_drivers):
                if not await self._check_driver(driver):
                    to_replace.append(driver)

            for driver in to_replace:
                self.logger.warning("♻️ Replacing broken driver")
                await self._replace_driver(driver)

            # 补足数量
            while self.drivers_queue.qsize() + len(to_replace) < self.max_drivers:
                new_driver = await self._create_driver_with_retry()
                if new_driver:
                    await self.drivers_queue.put(new_driver)
                    self.all_drivers.add(new_driver)

    async def shutdown(self):
        self.logger.info("🔻 Shutting down driver manager")
        self.monitoring = False
        while not self.drivers_queue.empty():
            driver = await self.drivers_queue.get()
            await self._safe_quit(driver)

        for driver in list(self.all_drivers):
            await self._safe_quit(driver)
        self.all_drivers.clear()

    async def _safe_quit(self, driver):
        await self.on_destroy(driver)
        try:
            driver.quit()
        except Exception as e:
            self.logger.warning(f"Failed to quit driver cleanly: {e}")

    async def on_create(self, driver):
        self.logger.info(f"🚀 Driver {id(driver)} initialized")

    async def on_destroy(self, driver):
        self.logger.info(f"🧹 Driver {id(driver)} destroyed")

# ✅ 上下文管理类：支持 async with
class AsyncDriverContext:
    def __init__(self, manager: AsyncDriverManager, driver):
        self.manager = manager
        self.driver = driver

    async def __aenter__(self):
        return self.driver

    async def __aexit__(self, exc_type, exc, tb):
        await self.manager.release_driver(self.driver)
