import sqlite3
from pathlib import Path
from src.config import config
from src.utils import logger

class Database:
    def __init__(self):
        self.db_path = Path(config.get("base.db_path", "avscraper.db"))

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """初始化数据库及所需的表。"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            logger.info(f"正在初始化数据库，路径：{self.db_path}...")
            
            # 创建 videos 表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS videos (
                    parsed_number TEXT PRIMARY KEY,
                    title TEXT,
                    description TEXT,
                    release_date TEXT,
                    director TEXT,
                    studio TEXT,
                    series TEXT,
                    category TEXT,
                    actors TEXT,
                    cover_url TEXT,
                    trailer_url TEXT,
                    image_urls TEXT,
                    scrape_status TEXT DEFAULT 'PENDING',
                    error_msg TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """)
            
            conn.commit()
            logger.info("数据库初始化成功。")
        except Exception as e:
            logger.error(f"数据库初始化失败：{e}")
            raise
        finally:
            conn.close()

db = Database()
