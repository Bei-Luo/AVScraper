import yaml
from pathlib import Path
from typing import Any, Dict

CONFIG_FILE = Path("config.yaml")


class Config:
    def __init__(self, config_path: Path = CONFIG_FILE):
        self.config_path = config_path
        self.data: Dict[str, Any] = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        default_config = {
            "base": {
                "scan_path": "./videos",
                "log_level": "DEBUG",
                "move_files": True,
                "generate_nfo": True,
                "download_cover": True,
                "download_trailer": True,
                "download_stills": True
            },
            "scraper": {
                "proxy": "",
                "timeout": 30,
                "max_retries": 3,
                "groups": {
                "javdb": {
                    "base_url": "https://javdb.com",
                    "search_url": "https://javdb.com/search?q={}&f=all",
                    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0"
                },
                "javbus": {
                    "base_url": "https://www.javbus.com",
                    "search_url": "https://www.javbus.com/{}",
                    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0"
                }
                },
                "enabled_crawlers": [
                "javdb",
                "javbus"
                ],
                "priority": {
                "title": [
                    "javdb",
                    "javbus"
                ],
                "description": [
                    "javdb",
                    "javbus"
                ],
                "release_date": [
                    "javdb",
                    "javbus"
                ],
                "director": [
                    "javdb",
                    "javbus"
                ],
                "studio": [
                    "javdb",
                    "javbus"
                ],
                "series": [
                    "javdb",
                    "javbus"
                ],
                "category": [
                    "javdb",
                    "javbus"
                ],
                "actors": [
                    "javdb",
                    "javbus"
                ],
                "cover_url": [
                    "javdb",
                    "javbus"
                ],
                "trailer_url": [
                    "javdb",
                    "javbus"
                ],
                "image_urls": [
                    "javdb",
                    "javbus"
                ]
                }
            },
            "scanner": {
                "min_size_mb": 0,
                "extensions": [
                ".mp4",
                ".mkv",
                ".avi",
                ".wmv",
                ".mov"
                ]
            }
            }
        if not self.config_path.exists():
            # 写入默认配置
            self.config_path.write_text(yaml.dump(default_config), encoding="utf-8")
            return default_config

        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or default_config

    def get(self, key: str, default: Any = None) -> Any:
        """
        通过点分隔的键获取配置值，例如 'base.scan_path'
        """
        keys = key.split(".")
        value = self.data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default


# 全局配置实例
config = Config()


def reload_config():
    global config
    config = Config()
