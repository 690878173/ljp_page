# HTTP Session AI Context

## 入口与模型

这是可插拔 HTTP 请求层。业务代码使用统一 Session、Pool、配置和响应模型；底层
实现通过 Adapter 隔离。推荐从 `ljp_page.request` 导入公开对象。

核心公开对象：

- `SyncSession` / `AsyncSession`：单会话请求入口。
- `SyncSessionPool` / `AsyncSessionPool`：池化入口，分别管理多个同步/异步 Session。
- `SessionConfig`：统一配置，包含 `Request`、`Timeout`、`Retry`、`Proxy`、`SessionPool`。
- `RequestsReponse`：所有后端统一返回的响应模型。保留该拼写，不要改为 `Response`。
- `RequestArgs`：只在 Session 与 Adapter 间传递的无后端依赖请求模型。

## 基本用法

```python
from ljp_page.request import SessionConfig, SyncSession

with SyncSession(SessionConfig()) as session:
    response = session.get("https://example.com", headers={"Accept": "application/json"})
    response.raise_for_status()
    data = response.json()
```

```python
from ljp_page.request import AsyncSession

async with AsyncSession() as session:
    response = await session.get("https://example.com")
```

```python
from ljp_page.request import AsyncSessionPool

async with AsyncSessionPool() as pool:
    response = await pool.get("https://example.com")
```

同步池使用 `with SyncSessionPool() as pool`；异步池使用 `async with AsyncSessionPool() as pool`。
Pool 的容量由 `SessionConfig.SessionPool.max_session` 决定。Pool 关闭后可再次 `open()`。

## 请求、配置与响应速查

所有 `request()`、`get()`、`post()`、`put()`、`patch()`、`delete()`、`head()`、`options()`
都返回 `RequestsReponse`；异步版本需要 `await`。常用请求参数如下：

| 参数 | 含义 |
| --- | --- |
| `headers` | 本次请求 Header，会按 requests 的大小写不敏感语义覆盖默认 Header |
| `cookies` | 本次请求 Cookie；不会取代 Adapter 托管的 CookieJar |
| `timeout` | 数值或 `(connect, read)` 元组；覆盖 `SessionConfig.Timeout` |
| `proxy` / `proxies` | 本次请求代理；优先级高于 `SessionConfig.Proxy` |
| `params`、`data`、`json` | 查询参数、请求体、JSON 请求体；`json` 与 `json_data` 不能同时传 |
| `allow_redirects`、`stream`、`verify_ssl` | 覆盖 `SessionConfig.Request` 对应默认值 |
| 其余 Adapter 支持的选项 | 作为中性 `RequestArgs.extra` 透传；不得让业务依赖某个后端专用返回类型 |

`SessionConfig` 的职责：

| 区段 | 管理内容 |
| --- | --- |
| `Request` | 默认 Header/Cookie、SSL、重定向、流式、延迟、环境代理、基础 URL 与额外选项 |
| `Timeout` | connect/read 默认超时与请求级覆盖解析 |
| `Retry` | 最大重试次数、异常匹配、回退延迟和回调 |
| `Proxy` | HTTP/HTTPS 默认代理与按 URL 协议选择 |
| `SessionPool` | 池容量与 Adapter 连接池相关参数 |

`RequestsReponse` 的稳定消费面是 `status_code`、`ok`、`url`、`headers`、`content`、`text`、
`json()`、`cookies`、`history`、`elapsed`、`retries`、`raise_for_status()` 和 `request_args`。
`raw` 仅供诊断，不得作为跨后端业务契约。

## 固定边界

- Session 构建 `RequestArgs`、处理重试与延迟、合并 Headers、委托 Cookie 操作和关闭资源。
- Adapter 内部创建并持有原生 `requests` / `aiohttp` / `curl-cffi` Session，负责网络 I/O、
  原生类型转换、统一响应构建及统一异常转换。
- 上层 Session、Pool 和业务代码不得访问 Adapter 的原生 session 对象。
- CookieJar 完全由 Adapter 托管。使用 `cookies`、`update_cookies()`、`clear_cookies()` 等公开 API 操作。
- Headers 每次请求都由上层合并并写入 `RequestArgs.headers`；不得依赖底层 session 默认 headers。
- 不添加旧 API 的兼容别名或旧配置映射。

## 错误、重试与生命周期

- Adapter 捕获底层异常并通过 `map_exception()` 转为项目统一异常；调用方不得捕获 requests、
  aiohttp 或 curl-cffi 专用异常作为主要控制流。
- Session 只对 `SessionConfig.Retry` 匹配的异常重试；HTTP 状态码本身不会自动变成重试条件。
- 重试会重新构建 `RequestArgs`，响应的 `retries` 记录实际重试次数，`elapsed` 是整次请求编排耗时。
- 单会话可显式 `open()`，但 `request()` 会确保已打开；同步对象用 `close()`，异步对象用
  `await close()`。推荐优先使用上下文管理器。
- Pool 会按容量创建多个独立 Adapter Session 并借还使用；不要从 Pool 的内部列表取得 Session。
  如确实传入 `session=`，调用方负责它的适配器类型和生命周期一致性。

## Adapter 选择

- `SyncSession` 默认使用 `RequestsAdapter`，只能传同步 Adapter。
- `AsyncSession` 默认使用 `AiohttpAdapter`；也可传异步 `CurlCffiAdapter`。
- Pool 的 `adapter` 参数是 Adapter 工厂或 Adapter 类；池中每个 Session 都创建自己的 Adapter。
- Adapter 必须实现 `BaseAdapter`，包括 `open`、`close`、`send`、Cookie 操作和 `map_exception`。

新增 Adapter 时，先实现 `BaseAdapter`，保持 `RequestArgs -> RequestsReponse` 的转换边界；
不要在 Session 或 Pool 中为新后端添加原生类型分支。异步 Adapter 设置 `is_async = True`，同步
Adapter 保持默认值；`SyncSession` 会拒绝异步 Adapter。

## 验证门

验证门仅属于 Pool 层，是可选业务编排，不属于 `SyncSession` / `AsyncSession` 的职责。

- 异步池默认持有 `AsyncVerification`；同步池默认持有 `SyncVerification`。
- 通过 `pool.verification.set_verification(checker, handler)` 注册。`checker` 只应识别真实的
  登录失效、验证码或风控响应，不能对所有响应返回真。
- `handler` 可以返回 `{"headers": {...}, "cookies": {...}}`，Pool 会通过公开 API 广播更新。
- 纯并发请求或性能测试应不注册验证门，或传 `verify_response=False`。

验证 handler 应只通过其返回值或 Pool 的公开 Header/Cookie 方法刷新状态。不要读取或修改
Adapter 的原生 CookieJar；这会破坏多后端一致性。高并发下验证门会暂停请求并可能重发，不能把它
当作常规响应回调。

## 修改定位

| 需求 | 首先查看 |
| --- | --- |
| 默认参数、Header 合并、重试和 URL 处理 | `base.py`、`config.py` |
| 同步/异步单会话生命周期 | `sync_client.py`、`async_client.py` |
| 统一请求/响应数据模型 | `models.py`、`types.py` |
| 同步/异步池与广播 Cookie/Header | `pool.py` |
| 验证门与并发暂停/重发 | `../verification.py` |
| Adapter 协议与具体后端 | `adapter/model.py`、`adapter/*.py` |

改动应遵循 `业务代码 -> Session/Pool -> Adapter -> 原生客户端` 的单向依赖。任何需要访问原生
session 的需求都应在 Adapter 内完成。

## 修改时同步

修改公开 Session/Pool 名称、`SessionConfig` 字段、Adapter 合同、Cookie/Header 规则、验证门行为、
重试语义或响应模型时，更新本文件；同步修改相关测试。
