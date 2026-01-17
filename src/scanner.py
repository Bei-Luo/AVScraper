import os
import re
from pathlib import Path
from typing import List, Optional
from src.config import config
from src.database import db
from src.utils import logger
from src.models import Video

class Scanner:
    def __init__(self):
        self.min_size_mb = config.get("scanner.min_size_mb", 100)
        self.extensions = set(config.get("scanner.extensions", [".mp4", ".mkv", ".avi", ".wmv", ".mov"]))
        # 匹配常见番号的正则 (例如: ABC-123, abc-123, ABC1234)
        # 2-5个字母，可选连字符，3-5个数字
        self.code_pattern = re.compile(r'([a-zA-Z]{2,5}-?\d{3,5})', re.IGNORECASE)

    def scan_directory(self, path: Path) -> int:
        """
        递归扫描目录中的视频文件并添加到数据库。
        返回新增视频的数量。
        """
        if not path.exists():
            logger.error(f"路径不存在：{path}")
            return 0

        logger.info(f"正在扫描目录：{path}")
        count = 0
        
        # 使用 get_file_map 逻辑来扫描，但这里我们需要逐个处理以添加到数据库
        #TODO: 这个函数遇到重复的番号时，会覆盖之前的记录，到时候要换 暂用
        file_map = self.get_file_map(path)
        for code, file_path_str in file_map.items():
            count += 1
            logger.debug(f"发现新视频：{code} ({file_path_str})")
        
        return file_map,count

    def get_file_map(self, path: Path) -> dict[str, str]:
        """
        扫描目录并返回 {parsed_number: file_path} 的映射。
        用于在运行时重新关联文件路径。
        """
        file_map = {}
        if not path.exists():
            return file_map

        for root, _, files in os.walk(path):
            for file in files:
                file_path = Path(root) / file
                
                if not self._is_video_file(file_path):
                    continue
                
                code = self._extract_code(file)
                if not code:
                    logger.warning(f"无法从文件中提取番号：{file}") # 减少日志噪音，可选
                    continue
                
                # 如果有重复番号，后面的会覆盖前面的，或者我们可以做更复杂的处理
                file_map[code] = str(file_path)
        
        return file_map

    def _is_video_file(self, file_path: Path) -> bool:
        if file_path.suffix.lower() not in self.extensions:
            return False
        
        try:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            if size_mb < self.min_size_mb:
                return False
        except OSError:
            return False
            
        return True

    def _extract_code(self, filename: str) -> Optional[str]:
        # 简单提取
        match = self.code_pattern.search(filename)
        if match:
            # 转换为大写
            return match.group(1).upper()
        return None