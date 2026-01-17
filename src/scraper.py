from asyncio import QueueShutDown
import time
import random
from typing import Optional, Dict, Any
from src.config import config
from src.database import db
from src.utils import logger
from src.models import Video
from src.nfo_gen import nfo_gen
from src.crawlers.javbus import Javbus
from src.crawlers.manager import CrawlerManager


class Scraper:
    def __init__(self):
        #TODO 根据配置文件初始化部分爬虫
        #初始化爬虫
        self.crawler_manager = CrawlerManager()
        self.crawler_manager.register_crawler(Javbus(config))

    def scrape_all(self,file_map: dict[str, str]):
        """刮削所有视频。"""

        for parsed_number, file_path in file_map.items():
            #构建视频文件信息
            video = Video(
                parsed_number=parsed_number,
                file_path=file_path,
                scrape_status="PENDING"
            )

            # 检查缓存是否存在
            if self._get_video_scrape(video):
                #缓存存在
                logger.info(f"视频 {video.parsed_number} 缓存，跳过刮削。")
            else:
                #缓存不存在
                logger.info(f"视频 {video.parsed_number} 缓存，开始刮削。")
                video = self.scrape_video(video)
            #生成nfo文件
            nfo_gen.generate_nfo(video)
            #下载资源文件
            #TODO 增加对多站点的支持 下载时需要根据字段使用的那个爬虫 来配置请求头
            nfo_gen.download_cover(video)
        
    def scrape_all_pending(self, file_map: dict[str, str]):
        """刮削所有状态为 PENDING (待处理) 的视频。"""
        pending_videos = self._get_pending_videos()
        if not pending_videos:
            logger.info("没有待处理的视频。")
            return

        logger.info(f"发现 {len(pending_videos)} 个待处理视频。")

        for video in pending_videos:
            try:
                # 尝试刮削视频
                self.scrape_video(video)
                # 随机延迟
                time.sleep(random.uniform(1, 3))
            except Exception as e:
                logger.error(f"视频 {video.parsed_number} 刮削失败：{e}")
                self._update_status(video.parsed_number, "FAILED", str(e))

    def scrape_video(self, video: Video)->Optional[Video]:
        logger.info(f"正在刮削元数据：{video.parsed_number}")
        
        # 使用 CrawlerManager 进行刮削
        metadata = self.crawler_manager.scrape(video.parsed_number)
        
        if not metadata:
            logger.warning(f"刮削失败：{video.parsed_number}")
            self._update_status(video.parsed_number, "FAILED", "所有爬虫均未找到结果")
            return None

        # 更新数据库
        self._update_video(video.parsed_number, metadata)
        logger.info(f"刮削成功：{video.parsed_number}")
        
        # 生成资源
        # 手动更新视频对象属性以便生成 NFO
        for k, v in metadata.items():
            setattr(video, k, v)
        return video

    def _get_pending_videos(self) -> list[Video]:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM videos WHERE scrape_status = 'PENDING'")
        rows = cursor.fetchall()
        conn.close()
        
        videos = []
        for row in rows:
            v = Video(
                parsed_number=row["parsed_number"],
                scrape_status=row["scrape_status"]
            )
            videos.append(v)
        return videos

    def _update_status(self, number: str, status: str, error: str = None):
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE videos SET scrape_status = ?, error_msg = ?, updated_at = ? WHERE parsed_number = ?",
            (status, error, time.strftime('%Y-%m-%d %H:%M:%S'), number)
        )
        conn.commit()
        conn.close()

    def _update_video(self, number: str, data: Dict[str, Any]):
        
        """
        更新视频记录，将刮削到的元数据写入数据库。
        """
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # 初始化固定字段：抓取状态和更新时间
        fields = ["scrape_status = ?", "updated_at = ?"]
        values = ["SUCCESS", time.strftime('%Y-%m-%d %H:%M:%S')]

        # 遍历传入的数据字典，根据键名动态拼接需更新的字段
        for k, v in data.items():
            if v is not None:
                fields.append(f"{k} = ?")
                # 如果v是字符串数组，先转为字符串
                if isinstance(v, list):
                    v = ','.join(v)
                values.append(v)
        values.append(number)
        
        sql = f"UPDATE videos SET {', '.join(fields)} WHERE parsed_number = ?"
        cursor.execute(sql, values)
        conn.commit()
        conn.close()
    def _get_video_scrape(self, video:Video)->bool:
        """根据parsed_number查询缓存状态"""
        conn = db.get_connection()
        cursor = conn.cursor()
        #查询视频缓存状态
        cursor.execute("SELECT * FROM videos WHERE parsed_number = ?", (video.parsed_number,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return False
        if row["scrape_status"]=="SUCCESS":
            row=dict(row)
            del row["parsed_number"]
            del row["scrape_status"]
            del row["error_msg"]
            del row["created_at"]
            del row["updated_at"]
            for k, v in row.items():
                setattr(video, k, v)
            return True
        return False