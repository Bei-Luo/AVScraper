from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Video:
    parsed_number: str  # 唯一标识（番号）
    file_path: Optional[str] = None  # 本地文件路径（不做持久化，运行时动态获取）
    title: Optional[str] = None
    description: Optional[str] = None
    release_date: Optional[str] = None
    director: Optional[str] = None
    studio: Optional[str] = None
    series: Optional[str] = None
    category: list[str] = None  # 可能为 list[str] 或字符串（兼容旧数据/序列化形式）
    actors: list[str] = None  # 可能为 list[str] 或字符串（兼容旧数据/序列化形式）
    cover_url: list[str] = None  # 约定为 [爬虫名, 封面URL]
    trailer_url: list[str] = None  # 约定为 [爬虫名, 预告片URL]
    image_urls: list[str] = None  # 约定为 [爬虫名, url1, url2, ...]；也可能为字符串（兼容旧数据/序列化形式）

    # 系统字段
    scrape_status: str = "PENDING"  # PENDING (待处理), SUCCESS (成功), FAILED (失败)
    error_msg: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self):
        return {
            "parsed_number": self.parsed_number,
            "file_path": self.file_path,
            "title": self.title,
            "description": self.description,
            "release_date": self.release_date,
            "director": self.director,
            "studio": self.studio,
            "series": self.series,
            "category": self.category,
            "actors": self.actors,
            "cover_url": self.cover_url,
            "trailer_url": self.trailer_url,
            "image_urls": self.image_urls,
            "scrape_status": self.scrape_status,
            "error_msg": self.error_msg,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
