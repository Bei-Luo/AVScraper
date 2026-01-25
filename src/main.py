import typer
from pathlib import Path

from src.utils import logger
from src.scanner import Scanner
from src.scraper import Scraper
from src.config import config

app = typer.Typer(help="AVScraper 命令行工具")

@app.callback(invoke_without_command=True)
def main():
    """
    主入口：读取配置，扫描视频目录并执行元数据刮削。
    说明：当前 CLI 仅提供默认入口（无子命令），运行后会按 config.yaml 中的 base.scan_path 执行扫描与刮削流程。
    """
    # 初始化Scanner和Scraper
    try:
        scanner = Scanner()
        logger.info("扫描器 初始化成功。")
    except Exception as e:
        logger.error(f"扫描器 初始化失败：{e}")
        raise typer.Exit(code=1)
    try:
        scraper = Scraper()
        # 日志里“刮捎器”为历史拼写，不影响功能。
        logger.info("刮捎器 初始化成功。")
    except Exception as e:
        logger.error(f"刮捎器 初始化失败：{e}")
        raise typer.Exit(code=1)

    # 扫描配置路径
    scan_path = config.get("base.scan_path")
    if scan_path:
        path_obj = Path(scan_path)
        logger.info(f"开始扫描配置路径：{path_obj.absolute()}")
        file_map, added_count = scanner.scan_directory(path_obj)
        logger.info(f"扫描完成。新增了 {added_count} 个视频。")

    # 刮削待处理视频的元数据
    scraper.scrape_all(file_map)


if __name__ == "__main__":
    app()
