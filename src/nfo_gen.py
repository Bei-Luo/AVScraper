import os
import requests
from pathlib import Path
from typing import Optional
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
            headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6",
            "cookie": "PHPSESSID=2m7sv6k1jrt1bji3p6sp61fnm4; existmag=mag",
            "Referer": "https://www.javbus.com/search/ACHJ-075"
            }
            #TODO 增加来源站点 否则会报错
            resp = requests.get(video.cover_url, timeout=30,headers=headers)

            resp.raise_for_status()
            
            with open(cover_path, "wb") as f:
                f.write(resp.content)
            logger.info(f"已保存封面: {cover_path}")
            
        except Exception as e:
            logger.error(f"下载封面失败 {video.parsed_number}: {e}")

nfo_gen = NFOGenerator()
