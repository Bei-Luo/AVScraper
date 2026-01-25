# AVScraper

一个基于命令行的本地视频文件元数据刮削与整理工具：从文件名中提取番号（如 `ABC-123`），到多个站点搜索并聚合元数据，随后按需生成 `.nfo`，下载封面/剧照/预告片，并可将视频文件归档到结构化目录中。

> 免责声明：本项目仅用于学习与个人资料整理。请遵守当地法律法规与目标站点的服务条款/robots 协议，避免对站点造成过大压力；涉及登录或成人确认时，请自行准备 Cookie，且不要将个人 Cookie 提交到仓库。

## 功能特性

- **番号识别**：递归扫描指定目录下的视频文件，从文件名中提取番号并统一转为大写。
- **多站点刮削与字段聚合**：支持多爬虫并行尝试，按字段优先级配置聚合结果（当前内置 `javdb`、`javbus`）。
- **媒体整理**：
  - 生成 Kodi / Emby / Jellyfin 常用的 `.nfo`（XML）。
  - 下载封面图（与视频同名 `.jpg`）。
  - 下载剧照到 `backdrops/` 目录。
  - 下载预告片为 `*-trailer.mp4`（基于 `yt-dlp`）。
- **可选归档**：可将视频移动到输出目录，并按 `演员/番号/文件` 的结构归档。
- **可配置**：使用 `config.yaml` 控制扫描、站点、代理、超时、字段优先级与输出行为。

## 项目结构

```
.
├─ main.py                # 程序入口：转发到 src.main 的 Typer app
├─ src/
│  ├─ main.py             # CLI：读取配置 -> 扫描 -> 刮削 -> 生成/下载/归档
│  ├─ config.py           # 配置加载：优先读取 config.yaml，不存在则生成默认配置
│  ├─ scanner.py          # 扫描器：提取番号并生成 {番号: 文件路径} 映射
│  ├─ scraper.py          # 刮削编排：调用爬虫聚合结果，按配置执行生成/下载/移动
│  ├─ models.py           # Video 数据模型（dataclass）
│  ├─ nfo_gen.py          # NFO 生成 + 封面/剧照/预告片下载
│  └─ crawlers/           # 站点爬虫实现（BaseCrawler + 各站点）
└─ config.yaml            # 运行配置（可自定义）
```

## 安装部署

### 方式 A：使用 uv（推荐）

仓库已包含 `pyproject.toml` 与 `uv.lock`，适合用 uv 进行可复现安装。

```bash
uv sync
```

如需严格按锁文件安装（推荐在 CI 或排查环境差异时使用）：

```bash
uv sync --frozen
```

如需在虚拟环境中执行：

```bash
uv run python main.py
```

### 方式 B：手动创建虚拟环境 + 安装依赖

PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
uv pip install -e .
```

Windows CMD：

```bat
python -m venv .venv
.\.venv\Scripts\activate.bat
uv pip install -e .
```

> 说明：请尽量从仓库根目录运行（`config.yaml` 以当前工作目录为基准加载）。

## 使用指南

### 1) 准备视频目录

- 默认扫描目录为 `./videos`（由 `base.scan_path` 控制）。
- 文件名需要包含番号（正则规则：`2-5` 个字母 + 可选 `-` + `3-5` 位数字），例如：
  - `ABC-123.mp4`
  - `abc1234.mkv`
  - `Some.Title.ABC-123.1080p.mp4`

### 2) 配置 `config.yaml`

首次运行若未找到 `config.yaml`，程序会自动生成一份默认配置；你也可以直接编辑仓库根目录下的 `config.yaml`。

常用项：

- `base.scan_path`：扫描目录
- `base.move_files`：是否将视频移动到输出目录（建议先设为 `false` 试跑）
- `base.output_path`：输出根目录（未配置时默认 `javoutp`）

### 3) 执行

```bash
uv run python main.py
```

执行流程（高层）：

1. 扫描目录 -> 提取番号 -> 生成 `{番号: 文件路径}` 映射
2. 逐个番号调用爬虫搜索并聚合字段
3. 按配置执行：移动文件 / 生成 NFO / 下载封面 / 下载预告片 / 下载剧照

### 4) 输出示例

默认输出目录为 `javoutp/`（可通过 `base.output_path` 修改），归档结构为：

```
javoutp/
  └─ 演员名/
     └─ ABC-123/
        ├─ ABC-123.mp4
        ├─ ABC-123.nfo
        ├─ ABC-123.jpg
        ├─ ABC-123-trailer.mp4
        └─ backdrops/
           ├─ 1.jpg
           ├─ 2.jpg
           └─ ...
```

## 配置说明

配置文件路径：运行目录下的 `config.yaml`。

### base

| 配置项 | 类型 | 默认值 | 说明 |
|---|---:|---:|---|
| `base.scan_path` | string | `./videos` | 扫描目录（建议使用绝对路径或明确相对路径） |
| `base.output_path` | string | `javoutp` | 输出目录根路径（代码内默认值） |
| `base.log_level` | string | `DEBUG/INFO` | 日志级别（RichHandler 输出） |
| `base.move_files` | bool | `true` | 是否移动视频文件到输出目录 |
| `base.generate_nfo` | bool | `true` | 是否生成 `.nfo` |
| `base.download_cover` | bool | `true` | 是否下载封面 |
| `base.download_trailer` | bool | `true` | 是否下载预告片 |
| `base.download_stills` | bool | `true` | 是否下载剧照 |

### scanner

| 配置项 | 类型 | 默认值 | 说明 |
|---|---:|---:|---|
| `scanner.min_size_mb` | number | `100` | 最小视频文件大小（MB）；过小会被忽略 |
| `scanner.extensions` | list | 常见视频后缀 | 允许扫描的后缀列表 |

### scraper

| 配置项 | 类型 | 默认值 | 说明 |
|---|---:|---:|---|
| `scraper.proxy` | string | `""` | 全局代理（如 `http://127.0.0.1:7890`） |
| `scraper.timeout` | number | `30` | 请求超时（秒） |
| `scraper.max_retries` | number | `3` | 失败重试次数 |
| `scraper.enabled_crawlers` | list | `["javdb","javbus"]` | 启用的爬虫（小写） |
| `scraper.priority` | object | - | 字段优先级：决定每个字段优先从哪个站点取值 |
| `scraper.groups.<site>` | object | - | 各站点的 base_url/search_url/headers/cookie 等 |

关于 Cookie：

- 部分站点需要登录或成人确认才能访问预告片/详情等资源。
- 建议仅在本地 `config.yaml` 中配置 Cookie，且不要将个人 Cookie 提交到版本库。

## 许可证

本项目采用 **GNU General Public License v3.0 (GPL-3.0)** 许可证，详见 [LICENSE](file:///F:/temp/test/LICENSE)。
