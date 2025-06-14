import requests


def crawl_page(url):
    """
    使用代理访问目标页面，并返回页面内容
    """
    proxies = {
        "http": "http://v2.api.juliangip.com/company/dynamic/getips?auto_white=1&num=1&pt=1&result_type=text&split=1&trade_no=1792764849634408&sign=9109f1d82d862b3263af357c9e1bfe22",
        "https": "http://v2.api.juliangip.com/company/dynamic/getips?auto_white=1&num=1&pt=1&result_type=text&split=1&trade_no=1792764849634408&sign=9109f1d82d862b3263af357c9e1bfe22"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "Cookie": "eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiIxNTk3MTAxOTQ5MCIsImlhdCI6MTc0OTczNDM4OCwiZXhwIjoxNzUyMzI2Mzg4fQ.LKUQtak6mJDnxr2je9tbptUw26XzMVLafdmPRGPNJwKlzcEfy2lu7iG5WInzcnZVt0PY4l1rXAVfVyq0A4nuFA"
    }
    try:
        response = requests.get(url, headers=headers,  timeout=15)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"请求页面失败: {e}")
        return None

if __name__ == '__main__':
    target_url =rf"https://www.tianyancha.com/nsearch?key=%E6%B3%A1%E6%B3%A1%E7%8E%9B%E7%89%B9"  # 修改为你要访问的页面地址
    content = crawl_page(target_url)
    if content:
        print(content)