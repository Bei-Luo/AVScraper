from asyncio import QueueShutDown
import time
import random
from typing import Optional, Dict, Any
from pathlib import Path
import shutil
from src.config import config
from src.database import db
from src.utils import logger
from src.models import Video
from src.nfo_gen import nfo_gen
from src.crawlers.javbus import Javbus
from src.crawlers.manager import CrawlerManager
import json


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
                #TODO 这个检查方法好像不太对
                scraped_video = self.scrape_video(video)
                if scraped_video is None:
                    continue
                video = scraped_video

            self._move_video_to_output(video)

            nfo_gen.generate_nfo(video)
            nfo_gen.download_cover(video)
            nfo_gen.download_trailer(video)
            nfo_gen.download_stills(video)
            
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
        """
        刮削视频元数据。
        """
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

        # 更新视频对象属性以便生成 NFO
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
                # 序列化字符串数组
                if isinstance(v, list):
                    v = json.dumps(v,ensure_ascii=False)
                values.append(v)
        values.append(number)
        # 先查询番号是否存在
        cursor.execute("SELECT 1 FROM videos WHERE parsed_number = ?", (number,))
        exists = cursor.fetchone() is not None
        if exists:
            # 存在则更新
            sql = f"UPDATE videos SET {', '.join(fields)} WHERE parsed_number = ?"
            cursor.execute(sql, values)
        else:
            # 不存在则插入
            insert_fields = ["parsed_number", "scrape_status","created_at","updated_at"]
            insert_values = [number, "SUCCESS", time.strftime('%Y-%m-%d %H:%M:%S'),time.strftime('%Y-%m-%d %H:%M:%S')]
            for k, v in data.items():
                if v is not None:
                    insert_fields.append(k)
                    if isinstance(v, list):
                        v = json.dumps(v,ensure_ascii=False)
                    insert_values.append(v)
            placeholders = ", ".join(["?"] * len(insert_fields))
            sql = f"INSERT INTO videos ({', '.join(insert_fields)}) VALUES ({placeholders})"
            cursor.execute(sql, insert_values)

        conn.commit()
        conn.close()

    def _get_video_scrape(self, video:Video)->bool:
        """根据parsed_number查询缓存状态，如果缓存命中，将缓存数据加载到视频对象中"""
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
            for k in ["category", "cover_url", "trailer_url","image_urls"]:
                if hasattr(video, k):
                    value = getattr(video, k)
                    if value:
                        setattr(video, k, json.loads(value))
            return True
        return False

    def _sanitize_for_path(self, name: str) -> str:
        if not name:
            return ""
        invalid_chars = '<>:"/\\|?*'
        result = "".join("_" if c in invalid_chars else c for c in str(name))
        return result.strip() or ""

    def _get_primary_actor_name(self, video: Video) -> str:
        actors = getattr(video, "actors", None)
        if not actors:
            return "未知演员"
        if isinstance(actors, list):
            first = actors[0] if actors else ""
            return self._sanitize_for_path(first) or "未知演员"
        if isinstance(actors, str):
            text = actors.strip()
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list) and parsed:
                    first = parsed[0]
                    return self._sanitize_for_path(first) or "未知演员"
            except Exception:
                pass
            first = text.split(",")[0]
            return self._sanitize_for_path(first) or "未知演员"
        return self._sanitize_for_path(str(actors)) or "未知演员"

    def _get_output_directory(self, video: Video) -> Path:
        base_output = config.get("base.output_path", "javoutp")
        root = Path(base_output)
        actor_name = self._get_primary_actor_name(video)
        number_dir = self._sanitize_for_path(video.parsed_number)
        return root / actor_name / number_dir

    def _move_video_to_output(self, video: Video):
        """将视频文件归类。"""
        if not video.file_path:
            logger.warning(f"视频 {video.parsed_number} 缺少文件路径，无法移动。")
            return
        src_path = Path(video.file_path)
        if not src_path.exists():
            logger.warning(f"视频文件不存在，无法移动：{src_path}")
            return

        target_dir = self._get_output_directory(video)
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / src_path.name

        if src_path.resolve() == target_path.resolve():
            logger.info(f"视频文件已在目标目录，无需移动：{target_path}")
            video.file_path = str(target_path)
            return

        try:
            shutil.move(str(src_path), str(target_path))
            video.file_path = str(target_path)
            logger.info(f"已移动视频文件到：{target_path}")
        except Exception as e:
            logger.error(f"移动视频文件失败 {video.parsed_number}: {e}")
