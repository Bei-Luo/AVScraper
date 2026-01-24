import os
import sys
import requests
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
import yt_dlp
from src.models import Video
from src.utils import logger
from src.config import config
import xml.etree.ElementTree as ET

def progress_hook(d):
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '').strip()
        eta = d.get('_eta_str', '').strip()
        speed = d.get('_speed_str', '').strip()
        # 使用 \r 回车符回到行首，实现单行刷新
        sys.stdout.write(f"\r下载进度: {percent} | 速度: {speed} | ETA: {eta}    ")
        sys.stdout.flush()
    elif d['status'] == 'finished':
        sys.stdout.write("\n")
        logger.info("下载完成，正在处理...")

class NFOGenerator:
    def generate_nfo(self, video: Video):
        if not video.file_path or not video.title:
            logger.warning(f"跳过生成 NFO {video.parsed_number}: 缺少路径或标题")
            return

        nfo_path = Path(video.file_path).with_suffix(".nfo")
        
        root = ET.Element("movie")
        ET.SubElement(root, "title").text = video.title
        ET.SubElement(root, "name").text = video.parsed_number
        ET.SubElement(root, "sorttitle").text = video.parsed_number
        ET.SubElement(root, "plot").text = video.description or ""
        ET.SubElement(root, "year").text = video.release_date[:4] if video.release_date else ""
        ET.SubElement(root, "releasedate").text = video.release_date or ""
        ET.SubElement(root, "studio").text = video.studio or ""
        ET.SubElement(root, "director").text = video.director or ""

        # 系列
        if video.series:
            ET.SubElement(root, "set").text = video.series

        # 类别
        if video.category:
            tags = video.category
            for tag in tags:
                ET.SubElement(root, "tag").text = tag.strip()

        # 演员
        if video.actors:
            actors_list = video.actors
            for actor_name in actors_list:
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

    def download_cover(self,crawler: Crawler, video:Video): 
        """
        下载视频封面并保存为 JPG 文件。
        封面路径规则：
        - 如果视频在自己的文件夹中，folder.jpg 最好。
        - 如果混合存放，filename-poster.jpg 或 filename.jpg
        - 这里使用 filename.jpg (封面)
        """
        if not video.file_path or not video.cover_url:
            return
        try:
            cover_path = Path(video.file_path).with_suffix(".jpg")
            # 简单检查避免重复下载
            if cover_path.exists():
                logger.info(f"封面已存在 {video.parsed_number}，跳过下载。")
                return

            logger.info(f"正在下载封面 {video.parsed_number}...")
            #更新请求头
            Referer=crawler.session.headers["Referer"]
            crawler.session.headers["Referer"]=crawler.detail_page
            resp = crawler._request(video.cover_url[1])
            crawler.session.headers["Referer"]=Referer
            resp.raise_for_status()
            
            with open(cover_path, "wb") as f:
                f.write(resp.content)
            logger.info(f"已保存封面: {cover_path}")
            
        except Exception as e:
            logger.error(f"下载封面失败 {video.parsed_number}: {e}")

    def download_trailer(self, crawler: Crawler, video: Video):
        """
        下载视频预告片并保存为 MP4 文件。
        预告片路径规则：
        - filename-trailer.mp4
        """
        if not video.file_path or not video.trailer_url:
            return

        try:
            video_path = Path(video.file_path)
            # 预告片命名规则: filename-trailer.mp4
            # 先确定目标文件路径（不带扩展名，由 yt-dlp 决定，但这里强制 mp4）
            trailer_path_template = video_path.with_name(f"{video_path.stem}-trailer.%(ext)s")
            final_trailer_path = video_path.with_name(f"{video_path.stem}-trailer.mp4")

            if final_trailer_path.exists():
                logger.info(f"预告片已存在 {video.parsed_number}，跳过下载。")
                return

            logger.info(f"正在下载预告片 {video.parsed_number}...")

            # 配置 yt-dlp
            ytdlp_opts = {
                'outtmpl': str(trailer_path_template),
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'merge_output_format': 'mp4',
                'quiet': True,
                'no_warnings': True,
                'progress_hooks': [progress_hook],
                # 忽略 SSL 错误，防止某些站点证书问题
                'nocheckcertificate': True,
            }
            # 优先使用手动设置的 Cookie
            manual_cookies=crawler.headers["Cookie"]
            if manual_cookies:
                ytdlp_opts.setdefault('http_headers', {})['Cookie'] = manual_cookies

            with yt_dlp.YoutubeDL(ytdlp_opts) as ydl:
                ydl.download([video.trailer_url[1]])
            
            logger.info(f"已保存预告片: {final_trailer_path}")

        except Exception as e:
            logger.error(f"下载预告片失败 {video.parsed_number}: {e}")

    def download_stills(self,crawler: Crawler, video: Video):
        """
        下载视频剧照并保存为 JPG 文件。
        剧照路径规则：
        - 如果视频在自己的文件夹中，filename-still-1.jpg 最好。
        - 如果混合存放，filename-1.jpg
        - 这里使用 filename-still-1.jpg (剧照)
        """
        if not video.file_path or not video.image_urls:
            return
        try:
            urls = video.image_urls
            urls = urls[1:]
            video_path = Path(video.file_path)
            for idx, url in enumerate(urls, start=1):
                parsed = urlparse(url)
                suffix = Path(parsed.path).suffix or ".jpg"
                still_path = video_path.with_name(video_path.stem + f"-still-{idx}" + suffix)
                if still_path.exists():
                    logger.info(f"剧照已存在 {video.parsed_number} 第 {idx} 张，跳过下载。")
                    continue
                logger.info(f"正在下载剧照 {video.parsed_number} 第 {idx} 张...")

                Referer=crawler.session.headers["Referer"]
                crawler.session.headers["Referer"]=crawler.detail_page
                resp = crawler._request(url)
                resp.raise_for_status()
                crawler.session.headers["Referer"]=Referer
                with open(still_path, "wb") as f:
                    f.write(resp.content)
            logger.info(f"剧照下载完成 {video.parsed_number}")
        except Exception as e:
            logger.error(f"下载剧照失败 {video.parsed_number}: {e}")

nfo_gen = NFOGenerator()
