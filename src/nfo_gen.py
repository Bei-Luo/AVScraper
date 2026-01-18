import os
import requests
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
from src.models import Video
from src.utils import logger
from src.config import config
import xml.etree.ElementTree as ET

class NFOGenerator:
    def generate_nfo(self, video: Video):
        if not video.file_path or not video.title:
            logger.warning(f"跳过生成 NFO {video.parsed_number}: 缺少路径或标题")
            return

        nfo_path = Path(video.file_path).with_suffix(".nfo")
        
        root = ET.Element("movie")
        ET.SubElement(root, "title").text = video.title
        ET.SubElement(root, "originaltitle").text = video.parsed_number
        ET.SubElement(root, "plot").text = video.description or ""
        ET.SubElement(root, "year").text = video.release_date[:4] if video.release_date else ""
        ET.SubElement(root, "releasedate").text = video.release_date or ""
        ET.SubElement(root, "studio").text = video.studio or ""
        ET.SubElement(root, "director").text = video.director or ""
        
        # 演员
        if video.actors:
            for actor_name in video.actors.split(","):
                actor = ET.SubElement(root, "actor")
                ET.SubElement(actor, "name").text = actor_name.strip()

        # 写入
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ", level=0)
        try:
            tree.write(nfo_path, encoding="utf-8", xml_declaration=True)
            logger.info(f"已生成 NFO: {nfo_path}")
        except Exception as e:
            logger.error(f"写入 NFO 失败 {video.parsed_number}: {e}")

    def download_cover(self, video: Video):
        if not video.file_path or not video.cover_url:
            return
        try:
            # Emby 使用 folder.jpg 或 filename-poster.jpg
            # 如果视频在自己的文件夹中，folder.jpg 最好。
            # 如果混合存放，filename-poster.jpg 或 filename.jpg
            # 这里使用 filename.jpg (封面)
            cover_path = Path(video.file_path).with_suffix(".jpg")
            
            # 简单检查避免重复下载
            if cover_path.exists():
                return

            logger.info(f"正在下载封面 {video.parsed_number}...")
            headers = video.cover_url[0]
            resp = requests.get(video.cover_url[1], timeout=30,headers=headers)

            resp.raise_for_status()
            
            with open(cover_path, "wb") as f:
                f.write(resp.content)
            logger.info(f"已保存封面: {cover_path}")
            
        except Exception as e:
            logger.error(f"下载封面失败 {video.parsed_number}: {e}")

    def download_trailer(self, video: Video):
        if not video.file_path or not video.trailer_url:
            return
        try:
            headers = None
            url = None
            if isinstance(video.trailer_url, (list, tuple)) and len(video.trailer_url) >= 2:
                headers = video.trailer_url[0]
                url = video.trailer_url[1]
            elif isinstance(video.trailer_url, str):
                url = video.trailer_url
            if not url:
                return
            parsed = urlparse(url)
            suffix = Path(parsed.path).suffix or ".mp4"
            video_path = Path(video.file_path)
            trailer_path = video_path.with_name(video_path.stem + "-trailer" + suffix)
            if trailer_path.exists():
                return
            logger.info(f"正在下载预告片 {video.parsed_number}...")
            if headers:
                resp = requests.get(url, timeout=30, headers=headers)
            else:
                resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            with open(trailer_path, "wb") as f:
                f.write(resp.content)
            logger.info(f"已保存预告片: {trailer_path}")
        except Exception as e:
            logger.error(f"下载预告片失败 {video.parsed_number}: {e}")

    def download_stills(self, video: Video):
        if not video.file_path or not video.image_urls:
            return
        try:
            headers = None
            urls = []
            if isinstance(video.image_urls, (list, tuple)) and len(video.image_urls) >= 2:
                headers = video.image_urls[0]
                urls_part = video.image_urls[1]
                if isinstance(urls_part, str):
                    urls = [u.strip() for u in urls_part.split(",") if u.strip()]
                else:
                    urls = list(urls_part)
            elif isinstance(video.image_urls, str):
                urls = [u.strip() for u in video.image_urls.split(",") if u.strip()]
            elif isinstance(video.image_urls, (list, tuple, set)):
                urls = list(video.image_urls)
            if not urls:
                return
            video_path = Path(video.file_path)
            for idx, url in enumerate(urls, start=1):
                parsed = urlparse(url)
                suffix = Path(parsed.path).suffix or ".jpg"
                still_path = video_path.with_name(video_path.stem + f"-still-{idx}" + suffix)
                if still_path.exists():
                    continue
                logger.info(f"正在下载剧照 {video.parsed_number} 第 {idx} 张...")
                if headers:
                    resp = requests.get(url, timeout=30, headers=headers)
                else:
                    resp = requests.get(url, timeout=30)
                resp.raise_for_status()
                with open(still_path, "wb") as f:
                    f.write(resp.content)
            logger.info(f"剧照下载完成 {video.parsed_number}")
        except Exception as e:
            logger.error(f"下载剧照失败 {video.parsed_number}: {e}")

nfo_gen = NFOGenerator()
