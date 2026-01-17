from abc import ABC, abstractmethod
from typing import Optional


class BaseCrawler(ABC):
    """
    所有爬虫的基类。
    定义了搜索和获取详情的接口。
    """

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
