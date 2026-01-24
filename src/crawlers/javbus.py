from typing import Optional
from urllib.parse import urljoin

from src.utils import logger
from src.crawlers.base import BaseCrawler

class Javbus(BaseCrawler):
    """
    Javbus爬虫实现。
    """

    def search(self, keyword: str) -> Optional[str]:
        """
        根据番号或关键字返回详情页 URL。
        """
        url = self.search_url.format(keyword)
        resp = self._request(url)
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

    def get_category(self, url: str) -> Optional[List[str]]:
        """获取类别/标签，多值时用英文逗号分隔。"""
        soup = self._get_soup(url).select('div.col-md-3')[0].find_all("p")[8].find_all("a")
        if soup:
            if len(soup)==1:
                soup=[soup[0].string.strip()]
            else:
                soup=[soup.string.strip() for soup in soup]
            return soup
        return None

    def get_actors(self, url: str) -> Optional[List[str]]:
        """获取演员名称，多名演员时用英文逗号分隔。"""
        soup = self._get_soup(url).select('div.col-md-3')[0].find_all("p")[10].find_all("a")
        if soup:
            if len(soup)==1:
                soup=[soup[0].string.strip()]
            else:
                soup=[soup.string.strip() for soup in soup]
            return soup
        return None

    def get_cover_url(self, url: str) -> Optional[List[str]]:
        """获取封面图片 URL。第一个放标识符"""
        #刮捎
        soup = self._get_soup(url)
        if not soup:
            return None
        img = soup.select_one(".bigImage img")
        if not img:
            return None
        src = img.get("src") or img.get("data-src")
        if not src:
            return None
        return [self.__class__.__name__, urljoin(self.base_url, src)]

    def get_trailer_url(self, url: str) -> Optional[List[str]]:
        """获取预告片视频 URL。第一个放标识符"""
        #刮捎
        soup = self._get_soup(url)
        if not soup:
            return None
        # 优先查找 video / source 标签
        video = soup.find("video")
        if video:
            source = video.find("source")
            src = (source.get("src") if source else None) or video.get("src")
            if src:
                return [self.__class__.__name__,urljoin(self.base_url, src)]
        # 回退：查找 href 中包含 preview 的链接
        a = soup.find("a", href=lambda x: x and "preview" in x)
        if a and a.get("href"):
            return [self.__class__.__name__,urljoin(self.base_url, a["href"])]
        return None

    def get_image_urls(self, url: str) -> Optional[List[str]]:
        """获取剧照图片 URL。第一个放标识符"""
        #刮捎
        
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
        urls.insert(0,self.__class__.__name__)
        return urls

    def main(self):
        """简单测试函数，用于验证爬虫是否正常工作。"""
        test_number = "ACHJ-075"
        url = self.search(test_number)
        
        if not url:
            print("未找到详情页 URL")
            return
        print(f"type:{type(url)}"+f"搜索到详情页 URL：{url}")
        print(f"type:{type(self.get_title(url))}"+f"标题：{self.get_title(url)}")
        print(f"type:{type(self.get_description(url))}"+f"简介：{self.get_description(url)}")
        print(f"type:{type(self.get_release_date(url))}"+f"发行日期：{self.get_release_date(url)}")
        print(f"type:{type(self.get_director(url))}"+f"导演：{self.get_director(url)}")
        print(f"type:{type(self.get_studio(url))}"+f"片商：{self.get_studio(url)}")
        print(f"type:{type(self.get_series(url))}"+f"系列：{self.get_series(url)}")
        print(f"type:{type(self.get_category(url))}"+f"类别：{self.get_category(url)}")
        print(f"type:{type(self.get_actors(url))}"+f"演员：{self.get_actors(url)}")
        print(f"type:{type(self.get_cover_url(url))}"+f"封面 URL：{self.get_cover_url(url)}")
        print(f"type:{type(self.get_trailer_url(url))}"+f"预告片 URL：{self.get_trailer_url(url)}")
        print(f"type:{type(self.get_image_urls(url))}"+f"剧照 URL：{self.get_image_urls(url)}")
        self.session.headers["Referer"]="https://www.javbus.com/ACHJ-075"
        # a["Referer"]="https://www.javbus.com/ACHJ-075"
        a=self._request(self.get_cover_url(url)[1])
        print(f"headers:{self.session.headers}")

if __name__ == "__main__":
    # 测试实例初始化
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
    spider = Javbus(config)
    spider.main()