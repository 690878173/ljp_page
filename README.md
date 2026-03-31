# ljp-page

`ljp-page` 是一个以“统一请求运行时”为核心的 Python 工具包，支持：

- 同步 / 异步请求统一封装
- 重试策略、日志等级、配置系统
- 中间件扩展（会话级 + 单次请求级）
- 统一响应对象与统一异常

---

## 安装

要求：`Python >= 3.12`

```bash
git clone <your-repo-url>
cd ljp_package
uv sync
```

或：

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

---

## 快速开始

### 1) 门面 Requests（最简单）

```python
from ljp_page.request import Requests

req = Requests()
res = req.get("https://www.baidu.com")

print(res.status_code)  # 默认返回 LjpResponse
print(res)              # 打印响应摘要，不包含正文内容
print(res.text[:100])   # 需要正文时再取
```

### 2) create_session（推荐进阶）

```python
from ljp_page.request import create_session

session = create_session("sync", base_url="https://httpbin.org")
res = session.get("/get")
print(res.status_code)
session.close()
```

---

## 常见问题配置（按需改）

## 1) 怎么改重试次数

```python
from ljp_page.request import create_session

session = create_session("sync", retry={"total": 5})
```

门面写法：

```python
from ljp_page.request import Requests

req = Requests(Requests.Config(max_retries=5))
```

## 2) 怎么改日志输出级别

```python
from ljp_page.request import create_session

session = create_session(
    "sync",
    log={
        "enabled_levels": [10, 15, 19],  # 只输出 warrior/error/critical
        "default_level": 10,
    },
)
```

常用等级：

- `1` = debug
- `5` = info
- `10` = warrior / warning
- `15` = error
- `19` = critical
- `20` = off（关闭）

## 3) 怎么控制默认内置中间件开关

```python
from ljp_page.request import create_session

session = create_session(
    "sync",
    middleware={
        "enable_request_middleware": True,
        "enable_response_middleware": True,
        "enable_logging_middleware": False,
        "enable_retry_middleware": True,
    },
)
```

说明：

- `request middleware`：规范 method、注入 `X-Trace-Id`
- `response middleware`：在响应头补 `X-Trace-Id`
- `logging middleware`：请求开始/结束/失败日志
- `retry middleware`：按配置自动重试

---

## 自定义中间件

支持两种方式：

- 会话级：`session.use(...)`（后续请求都生效）
- 单次请求级：`request(..., middlewares=[...])`（只本次生效）

### 同步示例

```python
from ljp_page.core.middleware import SyncMiddleware
from ljp_page.request import create_session


class MyMiddleware(SyncMiddleware):
    def handle(self, context, next_handler, session):
        context.headers["X-From"] = "my-middleware"
        resp = next_handler(context)
        return resp


session = create_session("sync")
session.use(MyMiddleware())  # 会话级注册

res1 = session.get("https://httpbin.org/get")
res2 = session.request(
    "GET",
    "https://httpbin.org/get",
    middlewares=[MyMiddleware()],  # 单次覆盖
)
session.close()
```

### 异步示例

```python
import asyncio
from ljp_page.core.middleware import AsyncMiddleware
from ljp_page.request import create_session


class MyAsyncMiddleware(AsyncMiddleware):
    async def handle(self, context, next_handler, session):
        context.headers["X-Async"] = "1"
        return await next_handler(context)


async def main():
    session = create_session("async")
    session.use(MyAsyncMiddleware())
    async with session:
        res = await session.get("https://httpbin.org/get")
        print(res.status_code)


asyncio.run(main())
```

---

## 响应对象与异常

## LjpResponse（默认返回）

常用字段/方法：

- `status_code`
- `headers`
- `text`
- `binary`
- `json()`
- `elapsed`
- `retries`
- `request.trace_id`

## LjpRequestException

统一异常，携带：

- `trace_id`
- `method`
- `url`
- `category`（如 timeout/network/proxy/ssl/parse）
- `retries`
- `elapsed`
- `status_code`

---

## 其他模块（简要）

### 验证码识别

```python
from ljp_page.captcha import yzm

with open("captcha.png", "rb") as f:
    print(yzm(f.read()))
```

### Playwright

```python
import asyncio
from ljp_page.playwright import Playwright


async def main():
    async with Playwright(headless=True) as pw:
        await pw.goto("https://example.com")
        page = await pw.get_page()
        print(await page.title())


asyncio.run(main())
```

### 线程池

```python
from ljp_page.threadpool import ThreadPool

with ThreadPool(max_workers=4) as pool:
    future = pool.submit(lambda x: x * 2, 21)
    print(future.result())  # 42
```

---

## 测试

```bash
pytest -q
```

---

## License

MIT
