# LJP Package

## Unified Request Sessions

### Sync Example

```python
from ljp_page._ljp_network.requests import create_session

with create_session(
    "sync",
    headers={"X-Trace-Source": "sync-demo"},
    retry={"total": 2, "backoff_factor": 0.2},
) as session:
    response = session.get("https://example.com")
    print(response.status_code, response.text)
```

### Async Example

```python
import asyncio

from ljp_page._ljp_network.requests import create_session


async def main() -> None:
    async with create_session(
        "async",
        headers={"X-Trace-Source": "async-demo"},
        retry={"total": 2, "backoff_factor": 0.2},
    ) as session:
        response = await session.get("https://example.com")
        print(response.status_code, response.json())


asyncio.run(main())
```

### Benchmark

Local loopback benchmark collected on 2026-03-10 with 200 requests at concurrency 20.

| Runtime | Transport | QPS | Peak memory |
| --- | --- | ---: | ---: |
| SyncSession | requests | 246.92 | 0.92 MB |
| AsyncSession | aiohttp | 278.77 | 1.80 MB |

综合性Python工具包，提供网络请求、数据分析、可视化、浏览器自动化等功能的统一封装。

## 功能特性

### 网络请求模块 (_ljp_network)
- **Requests封装**：支持同步/异步HTTP请求，内置代理、重试、超时等机制
- **Playwright自动化**：浏览器自动化封装，支持无头模式和自定义配置
- **验证码识别**：基于ddddocr的验证码识别功能

### 数据分析模块 (_ljp_data_analysis)
- **Pandas封装**：增强的DataFrame操作，提供便捷的数据分析接口
- **机器学习**：内置K-Means聚类算法实现
- **可视化工具**：
  - Matplotlib封装：支持中文显示、自定义配色
  - Pyecharts封装：交互式图表生成

### 应用模块 (_ljp_app)
- **教务系统**：教务系统相关功能封装
- **影视工具**：m3u8视频流解析与下载，支持ffmpeg合并
- **PC端应用**：学生端和管理端功能

### 工具模块 (_ljp_utils)
- **文件操作**：文件管理、压缩、参数校验等工具
- **日志系统**：统一的日志记录接口
- **数学工具**：常用数学计算函数
- **排序算法**：多种排序算法实现
- **解码工具**：各类编码解码功能

### UI模块 (_ljp_ui)
- **表格视图**：数据表格展示组件
- **课程UI**：课程相关界面组件
- **教务UI**：教务系统界面封装

### JavaScript处理 (_ljp_js)
- **JS执行器**：支持通过execjs或nodejs执行JavaScript代码

### 异步编程 (_ljp_async)
- **异步封装**：异步编程辅助工具和协程管理

## 环境要求

- Python >= 3.12
- Windows / Linux / macOS

## 安装

### 从源码安装

```bash
git clone https://github.com/yourusername/ljp-package.git
cd ljp-package
pip install -e .
```

### 安装开发依赖

```bash
pip install -e ".[dev]"
```

## 快速开始

### 网络请求

```python
from ljp_page import request

# 同步请求
response = request.get("https://example.com")
print(response.text)

# 异步请求
async def main():
    async with request.AsyncSession() as session:
        result = await session.get("https://example.com")
        print(await result.text())
```

### 数据分析

```python
from ljp_page import pandas as ljp_pd
import pandas as pd

df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
info = ljp_pd.Info(df)
summary = info.summary()
print(summary)
```

### 可视化

```python
from ljp_page import matplotlib, pyecharts

# Matplotlib图表
plt_chart = matplotlib.Matplotlib()
plt_chart.line(x=[1, 2, 3], y=[4, 5, 6], title="示例图表")

# Pyecharts交互图表
echart = pyecharts.Pyecharts()
bar = echart.bar(x=["A", "B", "C"], y=[10, 20, 30], title="柱状图")
bar.render("chart.html")
```

### 浏览器自动化

```python
from ljp_page import playwright
import asyncio

async def main():
    async with playwright.Playwright(headless=False) as pw:
        page = pw.page
        await page.goto("https://example.com")
        content = await page.content()
        print(content)

asyncio.run(main())
```

### 验证码识别

```python
from ljp_page import captcha

with open("captcha.png", "rb") as f:
    result = captcha.yzm(f.read())
    print(f"识别结果: {result}")
```

### JavaScript执行

```python
from ljp_page import js

js_handler = js.Js("script.js")
result = js_handler.call("functionName", arg1, arg2)
print(result)
```

## 项目结构

```
ljp_package/
├── ljp_page/
│   ├── _ljp_app/          # 应用模块
│   │   ├── jwxt/          # 教务系统
│   │   └── pc/            # PC端应用
│   │       ├── Xs/        # 学生端
│   │       └── Ys/        # 影视工具
│   ├── _ljp_async/        # 异步编程
│   ├── _ljp_coro/         # 协程相关
│   ├── _ljp_data_analysis/# 数据分析
│   │   ├── ml/            # 机器学习
│   │   ├── pandas/        # Pandas封装
│   │   └── visualization/ # 可视化
│   ├── _ljp_js/           # JavaScript处理
│   ├── _ljp_network/      # 网络模块
│   │   ├── captcha/       # 验证码识别
│   │   ├── playwright/    # 浏览器自动化
│   │   └── requests/      # HTTP请求
│   ├── _ljp_ui/           # UI模块
│   ├── _ljp_utils/        # 工具模块
│   └── outside/           # 对外接口
├── main.py                # 主程序入口
├── pyproject.toml         # 项目配置
└── README.md              # 项目文档
```

## 依赖库

- **requests**: HTTP请求库
- **aiohttp**: 异步HTTP请求
- **lxml**: HTML/XML解析
- **playwright**: 浏览器自动化
- **pandas**: 数据分析
- **numpy**: 数值计算
- **matplotlib**: 数据可视化
- **pyecharts**: 交互式图表
- **ddddocr**: 验证码识别

## 开发

### 运行测试

```bash
pytest
```

### 代码格式化

```bash
black .
```

### 代码检查

```bash
ruff check .
```

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来帮助改进本项目。

## 联系方式

- 作者: ljp
- 邮箱: ljp@example.com
