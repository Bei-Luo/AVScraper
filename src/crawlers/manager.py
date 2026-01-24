from typing import List, Optional, Dict, Any
from src import config
from src.crawlers.javbus import Javbus
from src.crawlers.javdb import Javdb
from src.crawlers.base import BaseCrawler
from src.utils import logger


class CrawlerManager:
    """
    管理多个爬虫实例。
    """

    def __init__(self,config):
        self.crawlers= {}
        #注册javdb爬虫
        crawlers_config={
            "base_url": config.get("scraper.groups.javdb.base_url"),
            "search_url": config.get("scraper.groups.javdb.search_url"),
            "headers": {
                "User-Agent": config.get("scraper.groups.javdb.User-Agent",""),
                "Accept-Language": config.get("scraper.groups.javdb.Accept-Language",""),
                "Cookie": config.get("scraper.groups.javdb.Cookie","")
            },
            "timeout": config.get("scraper.groups.javdb.timeout", config.get("scraper.timeout")),
            "max_retries": config.get("scraper.groups.javdb.max_retries", config.get("scraper.max_retries")),
            "proxy": config.get("scraper.groups.javdb.proxy", config.get("scraper.proxy"))
        }
        self.crawlers["Javdb"]=Javdb(crawlers_config)

        #注册javbus爬虫
        crawlers_config={
            "base_url": config.get("scraper.groups.javbus.base_url"),
            "search_url": config.get("scraper.groups.javbus.search_url"),
            "headers": {
                "User-Agent": config.get("scraper.groups.javbus.User-Agent",""),
                "Accept-Language": config.get("scraper.groups.javbus.Accept-Language",""),
                "Cookie": config.get("scraper.groups.javbus.Cookie","")
            },
            "timeout": config.get("scraper.groups.javbus.timeout", config.get("scraper.timeout")),
            "max_retries": config.get("scraper.groups.javbus.max_retries", config.get("scraper.max_retries")),
            "proxy": config.get("scraper.groups.javbus.proxy", config.get("scraper.proxy"))
        }
        self.crawlers["Javbus"]=Javbus(crawlers_config)



        
    def scrape(self, keyword: str) -> Optional[Dict[str, Any]]:
        """
        遍历所有注册的爬虫，尝试刮削数据。
        一旦某个爬虫成功获取数据，立即返回。
        """
        #TODO 重构为根据字段优先级搜索
        # 字段优先级配置：可指定多个站点，按顺序尝试
        self.field_priority: Dict[str, List[str]] = {
            "title": ["javbus", "javdb"],
            "description": ["javdb", "javbus"],
            "release_date": ["javbus"],
            "director": ["javbus"],
            "studio": ["javbus"],
            "series": ["javbus"],
            "category": ["javbus"],
            "actors": ["javbus", "javdb"],
            "cover_url": ["javbus", "javdb"],
            "trailer_url": ["javdb"],
            "image_urls": ["javdb", "javbus"],
        }
        # 启用的爬虫列表，可按需增删
        self.enabled_crawlers: List[str] = ["javbus", "javdb"]
        # 根据字段优先级，聚合各爬虫数据
        merged: Dict[str, Any] = {
            "title": None,
            "description": None,
            "release_date": None,
            "director": None,
            "studio": None,
            "series": None,
            "category": None,
            "actors": None,
            "cover_url": None,
            "trailer_url": None,
            "image_urls": None,
        }
        # 先收集所有爬虫结果
        crawler_results: Dict[str, Dict[str, Any]] = {}
        for name, crawler in self.crawlers.items():
            crawler_name = name
            if crawler_name.lower() not in self.enabled_crawlers:
                continue
            logger.info(f"尝试使用爬虫 {crawler_name} 搜索：{keyword}")
            try:
                detail_url = crawler.search(keyword)
                if not detail_url:
                    logger.debug(f"爬虫 {crawler_name} 未找到结果")
                    continue

                logger.info(f"爬虫 {crawler_name} 找到链接：{detail_url}")
                #更新详情页地址
                crawler.detail_page = detail_url
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
                crawler_results[crawler_name.lower()] = data
            except Exception as e:
                logger.error(f"爬虫 {crawler_name} 运行出错：{e}")
                continue

        # 按字段优先级填充 merged
        for field, priority_list in self.field_priority.items():
            for site in priority_list:
                if site in crawler_results and crawler_results[site].get(field) is not None:
                    merged[field] = crawler_results[site][field]
                    logger.info(f"字段 {field} 取自 {site}")
                    break

        # 只要有一个字段有值就返回
        if any(value is not None for value in merged.values()):
            logger.info("成功聚合字段")
            return merged

        logger.warning(f"所有爬虫均未找到：{keyword}")
        return None

if __name__ == "__main__":
    cm = CrawlerManager()