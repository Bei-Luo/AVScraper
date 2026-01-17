import os
import yaml
from pathlib import Path
from typing import Any, Dict

CONFIG_FILE = Path("config.yaml")

class Config:
    def __init__(self, config_path: Path = CONFIG_FILE):
        self.config_path = config_path
        self.data: Dict[str, Any] = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            # 如果文件不存在，返回默认值，或者抛出错误
            # 目前返回空字典，或者我们可以创建默认配置
            return {}
        
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

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
