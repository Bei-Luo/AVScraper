from asyncio import QueueShutDown
import time
import random
from typing import Optional, Dict, Any
from pathlib import Path
import shutil
import yt_dlp as ytdlp

from src.config import config
from src.utils import logger
from src.models import Video
from src.nfo_gen import nfo_gen
from src.crawlers.manager import CrawlerManager


class Scraper:
    def __init__(self):
        #TODO 根据配置文件初始化部分爬虫
        #初始化爬虫管理
        self.crawler_manager = CrawlerManager()

    def scrape_all(self,file_map: dict[str, str]):
        """刮削所有视频。"""

        for parsed_number, file_path in file_map.items():
            #构建视频文件信息
            video = Video(
                parsed_number=parsed_number,
                file_path=file_path,
                scrape_status="PENDING"
            )

            logger.info(f"视频 {video.parsed_number} ，开始刮削。")
            #TODO 这个检查方法好像不太对
            scraped_video = self.scrape_video(video)
            if scraped_video is None:
                continue
            video = scraped_video

            self._move_video_to_output(video)
            
            nfo_gen.generate_nfo(video)
            nfo_gen.download_cover(self,video)
            nfo_gen.download_trailer(self,video)
            nfo_gen.download_stills(self,video)
            
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
        logger.info(f"刮削成功：{video.parsed_number}")

        # 更新视频对象属性以便生成 NFO
        for k, v in metadata.items():
            setattr(video, k, v)
        return video

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
