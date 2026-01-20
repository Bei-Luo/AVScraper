from typing import List, Optional, Dict, Any
from src.crawlers.base import BaseCrawler
from src.utils import logger


class CrawlerManager:
    """
    管理多个爬虫实例。
    """

    def __init__(self):
        self.crawlers: List[BaseCrawler] = []
        #注册Javbus
        # TODO 先使用手动构建config 后面换用读取配置文件
        config={
            "base_url":"https://www.javbus.com",
            "search_url":"https://www.javbus.com/{}",
            "headers":{
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0",
                "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6",
            },
            "timeout": 10,
            "max_retries": 3,
        }
        self.crawlers.append(Javbus(config))
        del config
        config={
            "base_url":"https://www.javbus.com",
            "search_url":"https://www.javbus.com/{}",
            "headers":{
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0",
                "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6",
            },
            "timeout": 10,
            "max_retries": 3,
        }
        self.crawlers.append(Javdb(config))

        
    def scrape(self, keyword: str) -> Optional[Dict[str, Any]]:
        """
        遍历所有注册的爬虫，尝试刮削数据。
        一旦某个爬虫成功获取数据，立即返回。
        """
        #TODO 重构为根据字段优先级搜索
        for crawler in self.crawlers:
            crawler_name = type(crawler).__name__
            logger.info(f"尝试使用爬虫 {crawler_name} 搜索：{keyword}")
            try:
                detail_url = crawler.search(keyword)
                if not detail_url:
                    logger.debug(f"爬虫 {crawler_name} 未找到结果")
                    continue

                logger.info(f"爬虫 {crawler_name} 找到链接：{detail_url}")

                data: Dict[str, Any] = {
                    "title": crawler.get_title(detail_url),
                    "description": crawler.get_description(detail_url),
                    "release_date": crawler.get_release_date(detail_url),
                    "director": crawler.get_director(detail_url),
                    "studio": crawler.get_studio(detail_url),
                    "series": crawler.get_series(detail_url),
                    "category": crawler.get_category(detail_url),
                    "actors": crawler.get_actors(detail_url),
                    "cover_url": crawler.get_cover_url(detail_url),
                    "trailer_url": crawler.get_trailer_url(detail_url),
                    "image_urls": crawler.get_image_urls(detail_url),
                }

                if any(value is not None for value in data.values()):
                    logger.info(f"爬虫 {crawler_name} 成功获取详情")
                    return data
                else:
                    logger.warning(f"爬虫 {crawler_name} 获取详情失败")

            except Exception as e:
                logger.error(f"爬虫 {crawler_name} 运行出错：{e}")
                continue

        logger.warning(f"所有爬虫均未找到：{keyword}")
        return None
