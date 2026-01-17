import re
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any
from urllib.parse import urljoin
import sys
import os

# 将项目根目录添加到 sys.path，确保模块导入正常
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.utils import logger
from src.crawlers.base import BaseCrawler

class Javbus(BaseCrawler):
    """
    Javbus爬虫实现。
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
            "cookie": "PHPSESSID=2m7sv6k1jrt1bji3p6sp61fnm4; existmag=mag",
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
        # 简单的 Soup 缓存，按 URL 复用解析结果，避免重复请求同一详情页
        self._soup_cache = {}
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
    def _get_soup(self, url: str) -> Optional[BeautifulSoup]:
        """根据详情页 URL 返回 BeautifulSoup 对象，并按 URL 进行简单缓存。"""
        # 如果缓存中已有，直接复用，避免重复请求
        if url in self._soup_cache:
            return self._soup_cache[url]
        resp = self._request(url)
        if not resp:
            return None
        soup = BeautifulSoup(resp.text, "lxml")
        self._soup_cache[url] = soup
        return soup

    def search(self, keyword: str) -> Optional[str]:
        """
        根据番号或关键字返回详情页 URL。
        """
        url = self.search_url.format(keyword)
        resp = self._request(url)
        #测试
        a=self._request("https://www.javbus.com/pics/cover/bt57_b.jpg")
        pass
        if resp and resp.status_code == 200:
            return url
        return None

    def get_title(self, url: str) -> Optional[str]:
        """
        获取视频标题。
        """
        soup = self._get_soup(url)
        date = soup.find("h3")
        if date:
            return date.text.strip()
        return None

    def get_description(self, url: str) -> Optional[str]:
        """获取视频简介。Javbus 页面本身一般不提供简介，这里返回 None。"""
        return None

    def get_release_date(self, url: str) -> Optional[str]:
        """获取发行日期，格式建议：YYYY-MM-DD。"""
        soup = self._get_soup(url).select('div.col-md-3')[0].find_all("p")[1].find("span").next_sibling.string
        if soup:
            return soup.strip()
        return None

    def get_director(self, url: str) -> Optional[str]:
        """获取导演名称。"""
        soup = self._get_soup(url).select('div.col-md-3')[0].find_all("p")[3].find("a").string
        if soup:
            return soup.strip()
        return None

    def get_studio(self, url: str) -> Optional[str]:
        """获取制作商名称。"""
        soup = self._get_soup(url).select('div.col-md-3')[0].find_all("p")[4].find("a").string
        if soup:
            return soup.strip()
        return None


    # #TODO 发行商
    # def get_studio(self, url: str) -> Optional[str]:
    #     获取制作商名称。
    #     soup = self._get_soup(url).select('div.col-md-3')[0].find_all("p")[5].find("a").string
    #     if soup:
    #         return soup.strip()
    #     return None 

     
    def get_series(self, url: str) -> Optional[str]:
        """获取系列名称。"""
        soup = self._get_soup(url).select('div.col-md-3')[0].find_all("p")[6].find("a").string
        if soup:
            return soup.strip()
        return None

    def get_category(self, url: str) -> Optional[str]:
        """获取类别/标签，多值时用英文逗号分隔。"""
        soup = self._get_soup(url).select('div.col-md-3')[0].find_all("p")[8].find_all("a")
        if soup:
            if len(soup)==1:
                soup=soup[0].string.strip()
            else:
                soup=[soup.string.strip() for soup in soup]
            return soup
        return None

    def get_actors(self, url: str) -> Optional[str]:
        """获取演员名称，多名演员时用英文逗号分隔。"""
        soup = self._get_soup(url).select('div.col-md-3')[0].find_all("p")[10].find_all("a")
        if soup:
            if len(soup)==1:
                soup=soup[0].string.strip()
            else:
                soup=[soup.string.strip() for soup in soup]
            return soup
        return None

    def get_cover_url(self, url: str) -> Optional[str]:
        """获取封面图片 URL。"""
        soup = self._get_soup(url)
        if not soup:
            return None
        img = soup.select_one(".bigImage img")
        if not img:
            return None
        src = img.get("src") or img.get("data-src")
        if not src:
            return None
        return urljoin(self.base_url, src)

    def get_trailer_url(self, url: str) -> Optional[str]:
        """获取预告片视频 URL（如果有）。"""
        soup = self._get_soup(url)
        if not soup:
            return None
        # 优先查找 video / source 标签
        video = soup.find("video")
        if video:
            source = video.find("source")
            src = (source.get("src") if source else None) or video.get("src")
            if src:
                return urljoin(self.base_url, src)
        # 回退：查找 href 中包含 preview 的链接
        a = soup.find("a", href=lambda x: x and "preview" in x)
        if a and a.get("href"):
            return urljoin(self.base_url, a["href"])
        return None

    def get_image_urls(self, url: str) -> Optional[str]:
        """获取剧照图片 URL，多张图片时用英文逗号分隔。"""
        soup = self._get_soup(url)
        if not soup:
            return None
        imgs = soup.select("#sample-waterfall img")
        if not imgs:
            imgs = soup.select(".sample-box img")
        urls = []
        for img in imgs:
            src = img.get("src") or img.get("data-src")
            if src:
                full = urljoin(self.base_url, src)
                if full not in urls:
                    urls.append(full)
        if not urls:
            return None
        return ", ".join(urls)
    def main(self):
        """简单测试函数，用于验证爬虫是否正常工作。"""
        test_number = "ACHJ-075"
        url = self.search(test_number)
        
        if not url:
            print("未找到详情页 URL")
            return
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
        print(f"剧照 URL：{self.get_image_urls(url)}")

if __name__ == "__main__":
    # 测试实例初始化
    config = {
        "proxy": None,
        "timeout": 30
    }
    spider = Javbus(config)
    spider.main()