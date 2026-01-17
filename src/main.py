import typer
from pathlib import Path
import sys
import os

# 将项目根目录添加到 sys.path，确保模块导入正常
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from src.database import db
from src.utils import logger
from src.scanner import Scanner
from src.scraper import Scraper
from src.config import config

app = typer.Typer(help="AVScraper 命令行工具")

@app.command()
def init():
    """
    初始化数据库和项目结构。
    """
    try:
        db.init_db()
        logger.info("项目初始化成功。")
    except Exception as e:
        logger.error(f"初始化失败：{e}")
        raise typer.Exit(code=1)

@app.command()
def scan(path: str = typer.Option(None, help="扫描路径")):
    """
    扫描目录中的视频文件。
    """
    scan_path = path or config.get("base.scan_path")
    if not scan_path:
        logger.error("CLI 或配置中未提供扫描路径。")
        raise typer.Exit(code=1)
    
    path_obj = Path(scan_path)
    logger.info(f"开始扫描：{path_obj.absolute()}")
    
    added_count = scanner.scan_directory(path_obj)
    logger.info(f"扫描完成。新增了 {added_count} 个视频。")

@app.command()
def scrape():
    """
    刮削待处理视频的元数据。
    """
    scraper.scrape_all_pending()

@app.callback(invoke_without_command=True)
def main():
    """
    主入口，初始化数据库和项目结构。
    """
    #初始化数据库
    try:
        db.init_db()
        logger.info("数据库初始化成功。")
    except Exception as e:
        logger.error(f"数据库初始化失败：{e}")
        raise typer.Exit(code=1)
    
    #初始化Scanner和Scraper
    try:
        scanner = Scanner()
        logger.info("Scanner 初始化成功。")
    except Exception as e:
        logger.error(f"Scanner 初始化失败：{e}")
        raise typer.Exit(code=1)
    try:
        scraper = Scraper()
        logger.info("Scraper 初始化成功。")
    except Exception as e:
        logger.error(f"Scraper 初始化失败：{e}")
        raise typer.Exit(code=1)

    #扫描配置路径
    scan_path = config.get("base.scan_path")
    if scan_path:
        path_obj = Path(scan_path)
        logger.info(f"开始扫描配置路径：{path_obj.absolute()}")
        file_map,added_count = scanner.scan_directory(path_obj)
        logger.info(f"扫描完成。新增了 {added_count} 个视频。")

    #刮削待处理视频的元数据
    scraper.scrape_all(file_map)


if __name__ == "__main__":
    app()
