import logging
import time
from selenium_manager import SeleniumManager
from tianyan_Selenium import TianyanChaSpider

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    # 初始化WebDriver管理器
    selenium_manager = SeleniumManager(
        max_drivers=1,
        implicit_wait=10,
        page_load_timeout=30,
        headless=False  # 设为True可以在无界面模式运行
    )
    
    try:
        # 初始化天眼查爬虫
        spider = TianyanChaSpider(selenium_manager)
        
        # 示例：搜索公司
        companies = ["阿里巴巴"]
        
        for company_name in companies:
            print(f"正在搜索公司: {company_name}")
            result = spider.search_company(company_name)
            
            if result:
                print(f"公司信息: {result}")
            else:
                print(f"搜索公司 {company_name} 失败")
            
            # 避免请求过于频繁
            time.sleep(3)
            
    finally:
        # 确保关闭所有WebDriver实例
        selenium_manager.close_all()

if __name__ == "__main__":
    main()