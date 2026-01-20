from abc import ABC, abstractmethod
from typing import Any, Optional, Dict
import requests
import time
from bs4 import BeautifulSoup

from src.utils import logger



class BaseCrawler(ABC):
    """
    所有爬虫的基类。
    定义了搜索和获取详情的接口。
    """

    def __init__(self, config: Dict[str,Any]) -> None:
        """
        初始化类,配置基础信息。
        """
        self.config = config
        # 站点基础地址
        self.base_url = self.config["base_url"]
        # 站点搜索地址
        self.search_url = self.config["search_url"]
        # 请求头
        self.headers = self.config["headers"]
        # 设置Referer
        self.headers["Referer"] = self.base_url
        # 超时时间
        self.timeout = self.config.get("timeout", 10)
        # 最大重试次数
        self.max_retries = self.config.get("max_retries", 3)
        # 代理地址 如果有
        self.proxy = self.config.get("proxy", None)
        # 配置代理地址
        self.proxies={
            "http": self.proxy,
            "https": self.proxy,
        } if self.proxy else None
        # 简单的Soup缓存
        self._soup_cache = {}
        # 初始化 Session
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        if self.proxies:
            self.session.proxies.update(self.proxies)
        # 先访问首页获取cookie
        response=self._request(self.base_url)
        logger.debug(f"首页响应状态码: {response.status_code}")
        logger.info(f"初始化爬虫 {self.__class__.__name__} 完成")

    def _request(self, url: str) -> Optional[requests.Response]:
        """
        统一封装get请求,返回Response对象。
        实现重试机制,根据max_retries配置重试次数。
        """
        retries = 0
        while retries < self.max_retries:
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()

                return response
            except requests.RequestException as e:
                # TODO 连接 重试 暴力延时100ms
                print(response.text)
                time.sleep(0.1)

                retries += 1
                logger.error(f"请求 {url} 失败,第 {retries} 次重试: {e}")
        logger.error(f"请求 {url} 失败,超过最大重试次数 {self.max_retries}")
        return None

    def _get_soup(self, url: str) -> Optional[BeautifulSoup]:
        """
        获取 URL 的 BeautifulSoup 对象。
        主要用于获取详情页。
        实现缓存机制,避免重复请求。
        """
        # 检查缓存
        if url in self._soup_cache:
            return self._soup_cache[url]
        # 获取响应内容
        resp = self._request(url)
        if not resp:
            return None
        soup = BeautifulSoup(resp.text, "lxml")
        self._soup_cache[url] = soup
        return soup


    @abstractmethod
    def search(self, keyword: str) -> Optional[str]:
        """
        根据关键字（如番号）搜索视频。
        返回详情页的 URL，如果未找到则返回 None。
        """
        pass

    @abstractmethod
    def get_title(self, url: str) -> Optional[str]:
        """
        根据详情页 URL 获取标题。
        """
        pass

    @abstractmethod
    def get_description(self, url: str) -> Optional[str]:
        """
        根据详情页 URL 获取简介。
        """
        pass

    @abstractmethod
    def get_release_date(self, url: str) -> Optional[str]:
        """
        根据详情页 URL 获取发行日期。
        """
        pass

    @abstractmethod
    def get_director(self, url: str) -> Optional[str]:
        """
        根据详情页 URL 获取导演。
        """
        pass

    @abstractmethod
    def get_studio(self, url: str) -> Optional[str]:
        """
        根据详情页 URL 获取片商/工作室。
        """
        pass

    @abstractmethod
    def get_series(self, url: str) -> Optional[str]:
        """
        根据详情页 URL 获取系列。
        """
        pass

    @abstractmethod
    def get_category(self, url: str) -> Optional[str]:
        """
        根据详情页 URL 获取类别。
        """
        pass

    @abstractmethod
    def get_actors(self, url: str) -> Optional[str]:
        """
        根据详情页 URL 获取演员信息。
        """
        pass

    @abstractmethod
    def get_cover_url(self, url: str) -> Optional[str]:
        """
        根据详情页 URL 获取封面图片地址。
        """
        pass

    @abstractmethod
    def get_trailer_url(self, url: str) -> Optional[str]:
        """
        根据详情页 URL 获取预告片地址。
        """
        pass

    @abstractmethod
    def get_image_urls(self, url: str) -> Optional[str]:
        """
        根据详情页 URL 获取剧照图片地址列表（序列化为字符串）。
        """
        pass

