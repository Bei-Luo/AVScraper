from typing import Optional

from src.utils import logger
from src.crawlers.base import BaseCrawler
from typing import List


class Javdb(BaseCrawler):
    """
    Javdb 爬虫实现。
    """

    def _get_info(self, soup, key):
        """
        辅助函数：从详情页的信息面板中获取指定字段的节点。
        """
        if not soup:
            return None

        for block in soup.select(".movie-panel-info .panel-block"):
            strong = block.select_one("strong")
            if strong and key in strong.get_text():
                value_span = block.select_one(".value")
                if value_span:
                    return value_span
        return None

    def search(self, keyword: str) -> Optional[str]:
        """
        根据关键字（如番号）搜索视频。
        返回详情页的 URL，如果未找到则返回 None。
        """
        try:
            url = self.search_url.format(keyword)
            logger.info(f"正在搜索: {keyword}, URL: {url}")
            soup = self._get_soup(url)

            if not soup:
                logger.error(f"无法获取搜索结果页面: {url}")
                return None

            # 获取搜索结果列表
            items = soup.select(".movie-list .item")
            if not items:
                logger.warning(f"未找到相关影片: {keyword}")
                return None

            for item in items:
                # 检查番号是否匹配
                uid_node = item.select_one(".video-title strong")
                if not uid_node:
                    continue

                uid = uid_node.get_text(strip=True)

                # 简单对比番号，忽略大小写
                if uid.lower() == keyword.lower():
                    link_node = item.select_one("a")
                    if link_node:
                        href = link_node.get("href")
                        # 拼接完整 URL
                        if href.startswith("http"):
                            return href
                        return self.base_url.rstrip("/") + href

            return None

        except Exception as e:
            logger.error(f"搜索出错: {e}")
            return None

    def get_title(self, url: str) -> Optional[str]:
        """
        根据详情页 URL 获取标题。
        """
        soup = self._get_soup(url)
        if not soup:
            return None

        title_node = soup.select_one(".video-detail .title.is-4 .current-title")
        if title_node:
            return title_node.get_text(strip=True)
        return None

    def get_description(self, url: str) -> Optional[str]:
        """
        根据详情页 URL 获取简介。
        """
        # 当前实现未解析“简介/剧情”字段，直接返回 None；若后续确认站点提供对应区域，可在此补充 selector 并解析文本。
        return None

    def get_release_date(self, url: str) -> Optional[str]:
        """
        根据详情页 URL 获取发行日期。
        """
        soup = self._get_soup(url)
        value_node = self._get_info(soup, "日期")
        if value_node:
            return value_node.get_text(strip=True)
        return None

    def get_director(self, url: str) -> Optional[str]:
        """
        根据详情页 URL 获取导演。
        """
        soup = self._get_soup(url)
        value_node = self._get_info(soup, "導演")
        if value_node:
            return value_node.get_text(strip=True)
        return None

    def get_studio(self, url: str) -> Optional[str]:
        """
        根据详情页 URL 获取片商/工作室。
        """
        soup = self._get_soup(url)
        value_node = self._get_info(soup, "片商")
        if value_node:
            return value_node.get_text(strip=True)
        return None

    def get_series(self, url: str) -> Optional[str]:
        """
        根据详情页 URL 获取系列。
        """
        soup = self._get_soup(url)
        value_node = self._get_info(soup, "系列")
        if value_node:
            return value_node.get_text(strip=True)
        return None

    def get_category(self, url: str) -> Optional[List[str]]:
        """
        根据详情页 URL 获取类别。
        """
        soup = self._get_soup(url)
        value_node = self._get_info(soup, "類別")
        if value_node:
            # 提取所有链接文本
            tags = [a.get_text(strip=True) for a in value_node.select("a")]
            return tags
        return None

    def get_actors(self, url: str) -> Optional[List[str]]:
        """
        根据详情页 URL 获取演员信息。
        """
        soup = self._get_soup(url)
        value_node = self._get_info(soup, "演員")
        if value_node:
            # 提取所有链接文本，忽略性别符号等
            actors = [a.get_text(strip=True) for a in value_node.select("a")]
            return actors
        return None

    def get_cover_url(self, url: str) -> Optional[List[str]]:
        """
        根据详情页 URL 获取封面图片地址：返回 [爬虫名, 封面URL]，下游用第 0 项选择对应爬虫实例。
        """
        soup = self._get_soup(url)
        if not soup:
            return None

        cover_node = soup.select_one(".video-detail .column-video-cover .video-cover")
        if cover_node:
            return [self.__class__.__name__, cover_node.get("src")]
        return None

    def get_trailer_url(self, url: str) -> Optional[List[str]]:
        """
        根据详情页 URL 获取预告片地址：返回 [爬虫名, 预告片URL]，下游用第 0 项选择对应爬虫实例。
        """
        soup = self._get_soup(url)
        if not soup:
            return None

        # 调试用：保存详情页 HTML 到本地以便分析选择器/结构变化（会覆盖 debug_detail.html，建议仅在本地排查时启用）。
        if logger.isEnabledFor(10):
            with open("debug_detail.html", "w", encoding="utf-8") as f:
                f.write(str(soup))
        # 策略 1: 直接查找 id="preview-video" 的 video 标签
        # 登录后的页面通常会有这个标签
        video_node = soup.select_one("#preview-video")
        if video_node:
            source_node = video_node.select_one("source")
            if source_node:
                return [self.__class__.__name__, source_node.get("src")]

        # 策略 2：回退到预告片容器（用于页面结构差异，或未登录时缺少 #preview-video 的情况）
        trailer_node = soup.select_one(".preview-video-container")
        if trailer_node:
            # 可能是 video 标签或者 source 标签 (嵌套在容器内的情况)
            video_source = trailer_node.select_one("source")
            if video_source:
                return [self.__class__.__name__, video_source.get("src")]

            # 或者直接是 a 标签的 href (如果是 mp4 结尾)
            href = trailer_node.get("href")
            if href and (href.endswith(".mp4") or href.endswith(".m3u8")):
                return [self.__class__.__name__, href]

            # 有些可能是 data-src
            data_src = trailer_node.get("data-src")
            if data_src:
                return [self.__class__.__name__, data_src]

            # 如果链接跳转到登录页，说明需要登录权限
            if href == "/login":
                logger.warning(f"无法获取预告片: 需要登录权限 (URL: {url})")
                return None

        return None

    def get_image_urls(self, url: str) -> Optional[List[str]]:
        """
        根据详情页 URL 获取剧照图片地址列表：返回 [爬虫名, url1, url2, ...]，下游用第 0 项选择对应爬虫实例。
        """
        soup = self._get_soup(url)
        if not soup:
            return None

        images = []
        # 查找预览图部分
        preview_nodes = soup.select(".preview-images .tile-item")
        for node in preview_nodes:
            href = node.get("href")
            if href:
                images.append(href)

        if not images:
            return None
        images.insert(0, self.__class__.__name__)
        return images

    def main(self):
        """简单测试函数，用于验证爬虫是否正常工作。"""
        # 先访问首页刷新cookie
        self._get_soup(self.base_url)

        test_number = "ACHJ-075"
        url = self.search(test_number)

        if not url:
            print("未找到详情页 URL")
            return
        print(f"type:{type(url)}" + f"搜索到详情页 URL：{url}")
        print(f"type:{type(self.get_title(url))}" + f"标题：{self.get_title(url)}")
        print(
            f"type:{type(self.get_description(url))}"
            + f"简介：{self.get_description(url)}"
        )
        print(
            f"type:{type(self.get_release_date(url))}"
            + f"发行日期：{self.get_release_date(url)}"
        )
        print(
            f"type:{type(self.get_director(url))}" + f"导演：{self.get_director(url)}"
        )
        print(f"type:{type(self.get_studio(url))}" + f"片商：{self.get_studio(url)}")
        print(f"type:{type(self.get_series(url))}" + f"系列：{self.get_series(url)}")
        print(
            f"type:{type(self.get_category(url))}" + f"类别：{self.get_category(url)}"
        )
        print(f"type:{type(self.get_actors(url))}" + f"演员：{self.get_actors(url)}")
        print(
            f"type:{type(self.get_cover_url(url))}"
            + f"封面 URL：{self.get_cover_url(url)}"
        )
        print(
            f"type:{type(self.get_trailer_url(url))}"
            + f"预告片 URL：{self.get_trailer_url(url)}"
        )
        print(
            f"type:{type(self.get_image_urls(url))}"
            + f"剧照 URL：{self.get_image_urls(url)}"
        )


if __name__ == "__main__":
    # 测试实例初始化
    config = {
        "base_url": "https://javdb.com",
        "search_url": "https://javdb.com/search?q={}&f=all",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0",
            "Cookie": "list_mode=h; theme=auto; locale=zh",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Cache-Control": "max-age=0",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        },
        "timeout": 15,
        "max_retries": 3,
    }
    spider = Javdb(config)
    spider.main()
