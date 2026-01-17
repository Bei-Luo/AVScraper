import sys
import os


# 将项目根目录添加到 sys.path，确保模块导入正常
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.utils import logger
from src.crawlers.base import BaseCrawler

class CrawlerTemplate(BaseCrawler):
    """
    通用爬虫模板示例。
    复制本文件并根据目标站点实现各个方法。
    """
    def __init__(self, config: Dict[str, Any]):
        self.config=config
        # 站点基础地址，用于与相对路径通过 urljoin 拼接成完整链接
        self.base_url = "https://www.javbus.com"
        # 搜索地址模板，一般包含一个关键字占位符，如 ".../search?wd={}"
        self.search_url = "https://www.javbus.com/{}"
        # 请求头，目前只设置 User-Agent，避免被目标站点识别为爬虫
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6",
            "cookie": "",
        }
        # 如果配置了站点地址，则同时设置 Referer 头，模拟浏览器正常跳转
        if self.base_url:
            self.headers["Referer"] = self.base_url
        # 请求超时时间，避免网络问题导致长时间阻塞
        self.timeout = self.config.get("timeout", 30)
        # 代理地址（如果有），例如 "http://user:pass@host:port"
        self.proxy = self.config.get("proxy")
        # requests 所需的代理配置字典，如果没有配置代理则为 None
        self.proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
        logger.info(f"初始化爬虫 {self.__class__.__name__} 完成")

    def _request(self, url: str) -> Optional[requests.Response]:
        # 统一封装的 GET 请求方法，负责带上头信息、代理和超时时间
        try:
            resp = requests.get(
                url,
                headers=self.headers,
                proxies=self.proxies,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            # 状态码正常时返回 Response 对象
            return resp
        except requests.RequestException as e:
            # 捕获所有 requests 异常，记录日志方便排查
            logger.error(f"请求错误 {url}: {e}")
            return None

    def search(self, keyword: str) -> Optional[str]:
        """
        根据番号或关键字返回详情页 URL。
        """
        raise NotImplementedError("请在此实现搜索逻辑，返回详情页 URL")

    def get_title(self, url: str) -> Optional[str]:
        """
        获取视频标题。
        """
        raise NotImplementedError("请在此实现标题解析逻辑")

    def get_description(self, url: str) -> Optional[str]:
        """
        获取视频简介。
        """
        raise NotImplementedError("请在此实现简介解析逻辑")

    def get_release_date(self, url: str) -> Optional[str]:
        """
        获取发行日期，格式建议：YYYY-MM-DD。
        """
        raise NotImplementedError("请在此实现发行日期解析逻辑")

    def get_director(self, url: str) -> Optional[str]:
        """
        获取导演名称。
        """
        raise NotImplementedError("请在此实现导演解析逻辑")

    def get_studio(self, url: str) -> Optional[str]:
        """
        获取片商/工作室名称。
        """
        raise NotImplementedError("请在此实现片商解析逻辑")

    def get_series(self, url: str) -> Optional[str]:
        """
        获取系列名称。
        """
        raise NotImplementedError("请在此实现系列解析逻辑")

    def get_category(self, url: str) -> Optional[str]:
        """
        获取类别/标签，多值时建议用英文逗号分隔。
        """
        raise NotImplementedError("请在此实现类别解析逻辑")

    def get_actors(self, url: str) -> Optional[str]:
        """
        获取演员名称，多名演员时建议用英文逗号分隔。
        """
        raise NotImplementedError("请在此实现演员解析逻辑")

    def get_cover_url(self, url: str) -> Optional[str]:
        """
        获取封面图片 URL。
        """
        raise NotImplementedError("请在此实现封面 URL 解析逻辑")

    def get_trailer_url(self, url: str) -> Optional[str]:
        """
        获取预告片视频 URL（如果有）。
        """
        raise NotImplementedError("请在此实现预告片 URL 解析逻辑")

    def get_image_urls(self, url: str) -> Optional[str]:
        """
        获取剧照图片 URL，多张图片时建议用英文逗号分隔。
        """
        raise NotImplementedError("请在此实现剧照 URL 解析逻辑")
    def main(self):
        """
        测试函数，用于验证爬虫是否正常工作。
        """
        test_number = "ACHJ-075"
        print(f"测试番号：{test_number}")
        url = self.search(test_number)
        if url:
            print(f"搜索到详情页 URL：{url}")
            print(f"标题：{self.get_title(url)}")
            print(f"简介：{self.get_description(url)}")
            print(f"发行日期：{self.get_release_date(url)}")
            print(f"导演：{self.get_director(url)}")
            print(f"片商：{self.get_studio(url)}")
            print(f"系列：{self.get_series(url)}")
            print(f"类别：{self.get_category(url)}")
            print(f"演员：{self.get_actors(url)}")
            print(f"封面 URL：{self.get_cover_url(url)}")
            print(f"预告片 URL：{self.get_trailer_url(url)}")

if __name__ == "__main__":
    # 测试实例初始化
    config = {
        "proxy": None,
        "timeout": 30
    }
    spider = CrawlerTemplate(config)
    spider.main()

