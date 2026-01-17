# AVScraper v0.1 (MVP)

轻量级 Windows 命令行影片刮削工具。

## 功能特性
- **初始化**: 自动创建数据库和配置文件。
- **扫描**: 递归扫描目录，自动识别番号 (如 `ABC-123`)。
- **刮削**: 支持自定义站点 scraping (通过 `config.yaml` 配置 CSS 选择器)。
- **输出**: 生成 Emby/Jellyfin 兼容的 `.nfo` 文件并下载封面。

## 快速开始

### 1. 安装依赖
确保已安装 Python 3.9+。
```bash
pip install -r requirements.txt
# 或者如果使用 uv/poetry
uv sync
```

### 2. 初始化项目
在项目根目录运行：
```bash
python main.py init
```
这将创建 `avscraper.db` 和默认配置文件 `config.yaml`（如果不存在）。

### 3. 配置
修改 `config.yaml`：
- 设置 `base.scan_path` 为你的视频目录。
- 配置 `scraper` 部分的 `site_url`, `search_url` 和 `selectors` 以适配目标站点。

### 4. 扫描影片
```bash
python main.py scan --path "./videos"
```
或者直接使用配置文件中的路径：
```bash
python main.py scan
```

### 5. 刮削元数据
```bash
python main.py scrape
```
此命令会处理所有状态为 `PENDING` 的视频，抓取元数据并生成 NFO/封面。

## 开发指南
- `src/models.py`: 数据库模型
- `src/scanner.py`: 扫描逻辑
- `src/scraper.py`: 刮削逻辑
- `src/nfo_gen.py`: NFO 生成
- `src/config.py`: 配置管理

## 注意事项
- 默认 `min_size_mb` 为 100MB，测试时可在 config 中调整。
- 刮削器需要针对具体站点配置选择器。
