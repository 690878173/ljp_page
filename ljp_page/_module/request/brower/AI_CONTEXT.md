# Browser AI Context

## 目标与范围

`ljp_page._module.request.brower` 是浏览器自动化模块。它把浏览器、上下文和页面的
共同能力定义在 `base` 中，并由后端子包实现。本模块当前完整实现的是异步 Playwright
后端；`pydoll` 不属于这套接口，不要将它作为新接口设计或调用的依据。

当前设计的固定原则：

- 业务层使用包装对象的公共方法，而不是依赖 Playwright 的返回类型。
- 每个包装对象均有 `source`，它保存对应的原生对象。需要某个后端的独有能力时，只能
  通过 `source` 进入原生 API。
- 后端无关的值使用 `BrowserCookie`、`NavigationResult`、`FetchResult` 和
  `CDPResponseBody`；这些对象同样保存原始值的 `source`。
- CDP 的稳定入口是 `page.cdp`，浏览器上下文内请求的稳定入口是 `page.fetch`。
- 应用代码只从 `ljp_page.request.browser` 导入浏览器 API；`_module` 内部路径仅用于维护。

## 模块地图

| 位置 | 职责 |
| --- | --- |
| `base/model/async_api.py` | `AsyncBrowser`、`AsyncBrowserContext`、`AsyncPage`、`CDPSession` 的异步契约 |
| `base/model/types.py` | 通用 cookie、导航、fetch、CDP 返回值类型 |
| `base/model/browser.py` | 可插拔后端的同步 Browser / Context / Page 包装器 |
| `base/fingerprint/` | 后端无关的 CDP DOM 操作、挑战页契约和 Cloudflare profile |
| `playwright/browser.py` | 异步 Playwright 生命周期、浏览器与默认 Context |
| `playwright/context.py` | Playwright Context、headers/cookies、页面创建和 CDP session 创建 |
| `playwright/page.py` | Playwright Page、导航、DOM 常用动作、`cdp`、`fetch`、`solve_cloudflare()` |
| `playwright/cdp.py` | 高层 CDP 操作集合 |
| `playwright/request.py` | 在页面 JavaScript 环境中执行 Fetch API |
| `playwright/fingerprint.py` | 将基础 challenge 能力绑定到 Playwright Page |
| `playwright/verification.py` | fetch 并发验证门与 Cloudflare 响应识别 |

依赖方向必须保持为：

```text
业务代码 -> playwright 包装器 -> base 契约/值对象 -> 原生 Playwright
                           -> base/fingerprint
```

`base` 不能反向导入 `playwright`，也不能为了新后端向基础类型增加 Playwright 专用字段。

## 安装与导入

异步后端需要安装 Playwright 和目标浏览器。例如使用 Chromium：

```powershell
pip install playwright
playwright install chromium
```

唯一的应用层导入入口是：

```python
from ljp_page.request.browser import BrowserLaunchConfig, Playwright
```

该入口导出浏览器基础契约、标准返回类型、同步基础包装器以及当前 Playwright 实现。应用代码不应
从 `ljp_page._module.request.brower` 或 `ljp_page.request.browser.playwright` 导入。

所有异步 API 都必须在正在运行的事件循环中使用。浏览器、上下文、页面、CDP 和 fetch
调用均需要 `await`，推荐用 `async with` 确保关闭资源。

## 核心对象与生命周期

### 对象关系

一次普通启动会创建下面的对象链：

```text
Playwright
  └─ default_context: Ljp_Context
       └─ page: Ljp_Page
            ├─ cdp: PageCDP
            ├─ fetch: FetchRequest
            └─ fingerprint: PlaywrightFingerprint
                 └─ cloudflare: CloudflareChallenge
```

`Playwright.source` 是原生 `playwright.async_api.Browser`；持久化启动
(`user_data_dir` 非空) 时是原生 `BrowserContext`。`Ljp_Context.source` 是原生
`BrowserContext`，`Ljp_Page.source` 是原生 `Page`。`CDPSession.source` 是原生
Playwright CDP session。

### 最小可用示例

```python
import asyncio

from ljp_page.request.browser import BrowserLaunchConfig, Playwright


async def main() -> None:
    config = BrowserLaunchConfig(
        browser_type="chromium",
        channel=None,
        headless=True,
    )
    async with Playwright(config) as browser:
        page = await browser.new_page()
        result = await page.goto("https://example.com")

        print(result.url, result.status, result.ok)
        print(await page.title())
        print(await page.content())


asyncio.run(main())
```

`async with Playwright(config)` 会执行 `await start()`，退出时执行 `await close()`。普通
启动会关闭原生 browser 和自己创建的 Playwright runtime；如果构造函数传入外部 runtime，
包装器不会停止该 runtime。

也可以显式管理：

```python
browser = Playwright(BrowserLaunchConfig(browser_type="chromium", channel=None))
await browser.start()
try:
    page = await browser.new_page()
    await page.goto("https://example.com")
finally:
    await browser.close()
```

不要在 `browser.start()` 前访问 `default_context`、创建 Page 或读写 Browser 的 cookies。
`close()` 可重复调用。页面的 `close()` 会关闭它持有的缓存 CDP session 和原生 Page。

### 创建 Context 和 Page

`browser.new_page()` 从默认 Context 创建页面。`browser.new_context()` 创建隔离的
Playwright Context，因此 cookies、local storage、cache 与默认 Context 隔离：

```python
async with Playwright(BrowserLaunchConfig(browser_type="chromium", channel=None)) as browser:
    default_page = await browser.new_page()

    isolated = await browser.new_context(
        headers={"X-Tenant": "tenant-b"},
        cookies=[{"name": "session", "value": "abc", "url": "https://example.com"}],
    )
    isolated_page = await isolated.new_page(url="https://example.com")
    await isolated.close()
```

`Ljp_Context.new_page()` 只接受可选 `url=`；创建后若提供 URL 会立即导航。其他 Page
创建参数会抛出 `TypeError`，避免把 Context 或 Page 专用参数静默忽略。

持久化模式示例：

```python
config = BrowserLaunchConfig(
    browser_type="chromium",
    channel=None,
    user_data_dir="./runtime/browser-profile",
    headless=False,
)
async with Playwright(config) as browser:
    page = await browser.new_page()
```

持久化启动只有启动时创建的一个 Context。此时调用 `browser.new_context()` 会抛出
`RuntimeError`，不要试图创建多个隔离上下文。

## 配置

`BrowserLaunchConfig` 同时携带浏览器启动参数与默认 Context 参数。构造函数字段中，
`to_dict()` 只传给 `launch()` / `launch_persistent_context()`，`to_context_dict()` 只传给
`new_context()` / `launch_persistent_context()`。

常用字段：

| 字段 | 作用 |
| --- | --- |
| `browser_type` | `chromium`、`firefox` 或 `webkit`；CDP 能力通常仅适用于 Chromium 系 |
| `channel` | Playwright channel，例如 `msedge`；没有对应浏览器时显式传 `None` |
| `headless` | 是否无头启动 |
| `executable_path` | 浏览器可执行文件路径 |
| `args`、`ignore_default_args` | 原生浏览器启动参数 |
| `proxy`、`downloads_path`、`slow_mo`、`timeout` | Playwright launch 参数 |
| `user_data_dir` | 持久化 profile 路径；启用后不能创建额外 Context |
| `viewport`、`no_viewport`、`locale`、`timezone_id` | Context 环境参数 |
| `user_agent` | Context 初始 UA；运行中改 UA 使用 `page.cdp.set_user_agent()` |
| `extra_http_headers` | Context 默认 headers |
| `cookies` | 浏览器启动完成后写入默认 Context 的 cookies |
| `init_script` | 每个新文档执行的脚本 |
| `use_stealth_script` | 是否注入模块自带的 Playwright 初始化脚本 |

配置对象不校验浏览器路径和 channel 是否真实存在；启动失败会由 Playwright 抛出异常。不要把
CDP-only 配置写入 `BrowserLaunchConfig`，CDP 相关修改应通过 `page.cdp` 在页面创建后执行。

## 通用 Page API

`Ljp_Page` 的稳定公共方法如下：

| API | 返回值 | 说明 |
| --- | --- | --- |
| `page.url` | `str` | 当前 URL 属性 |
| `await page.title()` | `str` | 当前页面标题 |
| `await page.content()` | `str` | 当前 HTML |
| `await page.goto(url, ...)` | `NavigationResult` | 导航；默认等待 `domcontentloaded` |
| `await page.reload(...)` | `NavigationResult` | 重新加载；默认等待 `load` |
| `await page.evaluate(expression, arg=None)` | `Any` | 执行页面 JavaScript |
| `await page.click(selector, ...)` | `None` | 调用 Playwright Page.click |
| `await page.fill(selector, value, ...)` | `None` | 调用 Playwright Page.fill |
| `await page.wait_for_selector(selector, ...)` | 原生对象 | 返回 Playwright ElementHandle |
| `await page.screenshot(...)` | `bytes` | Playwright 原生截图 |
| `page.locator(selector)` | 原生对象 | 返回 Playwright Locator |
| `page.get_by_text(...)` / `page.get_by_role(...)` | 原生对象 | Playwright locator API |
| `await page.close()` | `None` | 关闭页面 |

导航结果使用 `NavigationResult`：

```python
navigation = await page.goto("https://example.com", wait_until="networkidle")
if navigation.ok is False:
    raise RuntimeError(f"navigation failed: {navigation.status}")
print(navigation.url, navigation.headers, navigation.source)
```

对于 `data:` 等没有 HTTP 响应的 URL，`status` 和 `ok` 都是 `None`。`source` 是原生
Playwright `Response`，没有响应时为 `None`。

## Headers 与 Cookies

Browser、Context 与 Page 都提供相同的 cookies/headers 主接口。实际状态属于 Context，
Page 与 Browser 的对应方法只是委托到默认 Context 或所属 Context。

```python
await page.set_headers({"Accept": "application/json", "X-Trace": "request-1"})
await page.update_headers({"X-Trace": "request-2"})
print(page.headers)

await page.set_cookies(
    [
        {
            "name": "session",
            "value": "token-value",
            "url": "https://example.com",
            "httpOnly": True,
            "sameSite": "Lax",
        }
    ]
)
cookies = await page.cookies(["https://example.com"])
for cookie in cookies:
    print(cookie.name, cookie.value, cookie.domain, cookie.source)

await page.clear_cookies()
```

规则：

- `set_headers()` 替换 Context 的完整 extra headers；要保留已有 header 并追加字段，使用
  `update_headers()`。
- `headers` 是普通 `dict[str, str]` 的快照，修改 `page.headers` 返回值不会写回浏览器。
- `set_cookies()` 接受 `BrowserCookie` 或 Playwright cookie mapping。Playwright 要求每个
  cookie 至少有可用的 `url`，或者提供有效的 `domain` 与 `path`。
- `cookies()` 返回 `list[BrowserCookie]`，而不是 Playwright dict。需要原始字段时使用
  `cookie.source`；需要再次写入时可直接把 `BrowserCookie` 交给 `set_cookies()`。
- `page.fetch` 会运行在当前页面的浏览器上下文中，通常共享该 Context 的认证 cookies。
`FetchResult.cookies` 仅来自 `document.cookie`，因此不包含 HttpOnly cookie；真实 cookie
状态应通过 `await page.cookies()` 查询。

### 验证后获取状态并请求详情页

验证通过后不需要手动拼接 `Cookie`，`page.fetch` 会在当前 Browser Context 中自动携带 cookies：

```python
detail_url = "https://www.bz444444444.com/57/57748/"

passed = await page.solve_cloudflare(timeout=30, poll_interval=0.5, max_attempts=3)
if not passed:
    raise RuntimeError("Cloudflare challenge was not resolved")

# cookies() 的参数是 URL 序列；单个 URL 要写成 [detail_url]。
cookies = await page.cookies([detail_url])
cookie_values = {cookie.name: cookie.value for cookie in cookies}

# page.headers 是 Context 配置的默认 extra headers 快照，不是浏览器自动生成的完整
# User-Agent、Accept、Cookie 等最终线级请求头。
context_headers = page.headers

response = await page.fetch.get(detail_url, timeout=30)
print(response.status, response.ok)
print(response.headers)       # 服务端响应 headers
print(response.encoding)      # 例如 gbk
print(response.text[:500])    # 已按响应 charset 解码
print(len(response.content))  # 原始 bytes 长度
```

该流程中 `page.fetch.get()` 默认使用 `credentials="include"`，因此会带上已通过验证的
`cf_clearance` 和其他上下文 cookies。`response.cookies` 只表示页面 JavaScript 可读取的
`document.cookie` 快照，不应拿它判断 HttpOnly cookies 是否存在；需要完整 cookie 列表时使用
`page.cookies()` 返回的 `BrowserCookie` 对象。上面的详情 URL 实测返回 HTTP `200`，响应正文为
`text/html; charset=gbk`。

## 原生对象边界

包装器没有试图复制 Playwright 的全部 API。后端独有场景可使用 `source`：

```python
async def allow_request(route) -> None:
    await route.continue_()

await page.source.route("**/*", allow_request)
native_context = page.context.source
native_page = page.source
```

`source` 是唯一的原生对象入口。业务代码不能读取 `_runtime`、`_browser`、`_contexts`、
`_pages`、`_cdp_session` 等私有状态，也不能把原生对象作为跨后端公共返回类型。

通过 `source` 调用原生 API 后，调用方负责理解该 API 的生命周期和副作用。例如，直接关闭
`page.source` 后，包装器不会自动更新自己的 `closed` 标记。

## CDP

### 获取与关闭 session

使用 `page.cdp` 处理常见 CDP 操作。需要低级会话时使用 `await page.get_cdp_session()`：

```python
session = await page.get_cdp_session()
try:
    result = await session.send("Runtime.evaluate", {
        "expression": "document.title",
        "returnByValue": True,
    })
    print(result["result"]["value"])
finally:
    await session.close()
```

`CDPSession.send()` 接受 CDP 方法字符串，也接受项目 `base.commands` 产生的 command mapping。
命令中的协议 `id` 与 `sessionId` 会被忽略，由底层 session 管理。`CDPSession.source` 是原生
Playwright CDPSession；`close()` 与 `detach()` 等价。

`page.get_cdp_session()` 的无参结果由 Page 缓存。通常不需要手动关闭缓存 session，关闭 Page
时会自动 detach。对 frame 或其他 target 调用 `await page.get_cdp_session(target)` 会创建目标
session；调用方应在使用完后 `await session.close()`。

CDP 只应在 Chromium 系浏览器上使用。Firefox/WebKit 不能假定兼容 Chrome DevTools Protocol。

### 常用高层 API

`PageCDP` 以稳定方法覆盖常见操作：

| API | 返回值 | 说明 |
| --- | --- | --- |
| `await page.cdp.send(method, params=None)` | `dict` | 任意原始 CDP 命令 |
| `await page.cdp.enable(dom=..., network=..., page=..., runtime=...)` | `None` | 按需启用 CDP domain |
| `await page.cdp.evaluate(expression, **options)` | `dict` | `Runtime.evaluate`；默认 `returnByValue=True`、`awaitPromise=True` |
| `await page.cdp.document(depth=-1, pierce=True)` | `dict` | `DOM.getDocument` |
| `await page.cdp.query_selector(node_id, selector)` | `int | None` | 节点范围内 querySelector |
| `await page.cdp.outer_html(node_id=None)` | `str` | 节点或根文档 HTML |
| `await page.cdp.layout_metrics()` | `dict` | 页面布局指标 |
| `await page.cdp.navigation_history()` | `dict` | CDP 导航历史 |
| `await page.cdp.capture_screenshot(...)` | `bytes` | CDP 截图，已 base64 解码 |
| `await page.cdp.capture_snapshot(format="mhtml")` | `str` | MHTML 页面快照 |
| `await page.cdp.print_to_pdf(**options)` | `bytes` | PDF，已 base64 解码 |
| `await page.cdp.set_bypass_csp(enabled=True)` | `dict` | 切换 CSP bypass |
| `await page.cdp.set_user_agent(ua, **options)` | `dict` | `Emulation.setUserAgentOverride` |
| `await page.cdp.set_extra_headers(headers)` | `dict` | CDP Network 额外 headers |
| `await page.cdp.set_cache_disabled(disabled=True)` | `dict` | 禁用/恢复 Network cache |
| `await page.cdp.clear_browser_cache()` | `dict` | 清理 CDP browser cache |
| `await page.cdp.get_cookies(urls=None)` | `list[BrowserCookie]` | CDP Network cookies |
| `await page.cdp.clear_cookies()` | `dict` | 清理 CDP browser cookies |
| `await page.cdp.response_body(request_id)` | `CDPResponseBody` | 按 Network requestId 获取 body |
| `await page.cdp.subscribe(event, handler)` | `Callable[[], None]` | 注册事件，返回取消订阅函数 |

### DOM、Runtime 与截图示例

```python
await page.goto("https://example.com")
await page.cdp.enable(dom=True, runtime=True, page=True)

document = await page.cdp.document(depth=0)
root_id = document["root"]["nodeId"]
main_id = await page.cdp.query_selector(root_id, "main")
if main_id is not None:
    print(await page.cdp.outer_html(node_id=main_id))

value = await page.cdp.evaluate("window.location.href")
print(value["result"]["value"])

png = await page.cdp.capture_screenshot(format="png")
with open("page.png", "wb") as file:
    file.write(png)

pdf = await page.cdp.print_to_pdf(printBackground=True)
with open("page.pdf", "wb") as file:
    file.write(pdf)
```

调用 `set_extra_headers()` 会修改 CDP Network 层；常规浏览器上下文 headers 应优先使用
`await page.set_headers()` / `await page.update_headers()`。两种机制都使用时，最终请求头由
浏览器/CDP 的实际合并行为决定，不应依赖同名字段的覆盖顺序。

### 获取 Network 响应体

必须先启用 Network 并从事件中保存 `requestId`。响应体只在 CDP 可用期间取得，过晚读取可能
被浏览器丢弃：

```python
request_ids: list[str] = []

def on_response(event: dict) -> None:
    request_ids.append(event["requestId"])

await page.cdp.enable(network=True)
unsubscribe = await page.cdp.subscribe("Network.responseReceived", on_response)
try:
    await page.goto("https://example.com")
    body = await page.cdp.response_body(request_ids[-1])
    print(body.request_id, body.base64_encoded, body.text)
finally:
    unsubscribe()
```

`CDPResponseBody.content` 是 bytes，`text` 使用 UTF-8 与替换策略解码。二进制资源应消费
`content`，不要使用 `text`。

## 浏览器上下文 Fetch

`page.fetch` 在当前 Page 的 JavaScript 世界调用浏览器 `fetch()`。它适合使用已经登录的
浏览器 session 请求接口：认证 cookies、页面状态和默认 browser credentials 会被带入请求。

```python
response = await page.fetch.get(
    "https://example.com/api/items",
    params={"page": "1"},
    headers={"Accept": "application/json"},
    timeout=15,
)
response.raise_for_status()
payload = response.json()
```

常用方法：`get`、`post`、`put`、`patch`、`delete`、`head`、`options`，以及底层
`request(method, url, ...)`。所有方法返回 `FetchResult`。

### 请求体与参数

```python
created = await page.fetch.post(
    "https://example.com/api/items",
    json={"name": "item"},
    headers={"X-Request-ID": "req-1"},
)

form_response = await page.fetch.post(
    "https://example.com/form",
    data={"username": "alice", "tags": ["a", "b"]},
)

binary_response = await page.fetch.put(
    "https://example.com/upload",
    data=b"binary payload",
    allow_redirects=False,
)
```

参数规则：

| 参数 | 语义 |
| --- | --- |
| `params` | 追加到 URL query string |
| `data` | `Mapping` 或二元 tuple 序列会编码为 form；`str` 直接作为 body；`bytes` 以字节数组传入页面 |
| `json` | JSON 序列化并默认设置 `content-type: application/json` |
| `headers` | 本次 Fetch 的 headers，不会修改 Context 的默认 headers |
| `timeout` | 秒；在页面中用 AbortController 实现 |
| `allow_redirects` | 映射到 Fetch 的 `redirect`，真为 `follow`，假为 `manual` |
| `check_fp` | 是否让验证门检查响应，默认真 |
| `verify_response` | 显式覆盖 `check_fp` |
| `verify_max_retries` | 覆盖验证门重试次数 |
| 其余 `**options` | 原样作为 Fetch API options，例如 `credentials`、`mode`、`cache`、`redirect` |

`data` 与 `json` 不能同时设置，会抛出 `ValueError`。浏览器 fetch 仍然遵守页面安全模型：CORS、
mixed content、same-origin 规则、禁止脚本设置的 headers 和 Service Worker 都可能影响结果。
需要绕过浏览器网络策略的场景应使用 HTTP Session 模块，不要错误地把 `page.fetch` 当作
`requests` 的替代品。

### FetchResult

```python
response = await page.fetch.get("https://example.com/api/profile")
print(response.url, response.status, response.ok)
print(response.headers)
print(response.encoding)
print(response.text)
print(response.json())
raw_body = response.content
raw_fetch_value = response.source
```

| 字段/方法 | 含义 |
| --- | --- |
| `url`、`status`、`headers` | 浏览器 Fetch 返回的最终 URL、状态和 headers |
| `content` | 始终为 bytes |
| `text` | 按 content-type charset 解码；无 charset 时 UTF-8 替换解码 |
| `encoding` | content-type 中的 charset，未知时 `None` |
| `json()` | 对 `text` 调用 JSON 解析 |
| `ok` | 状态在 `[200, 400)` 时为真 |
| `raise_for_status()` | 非 ok 时抛 `RuntimeError`，成功时返回自身，支持链式调用 |
| `cookies` | 页面可读的 `document.cookie` 快照，不包含 HttpOnly cookies |
| `source` | 页面 evaluate 返回的 JSON-like 原始值 |

请求无法在浏览器中完成时抛出 `FetchError`，它是 `HTTP_Fetch_error` 的子类。收到 HTTP 4xx/5xx
响应时仍会返回 `FetchResult`；用 `raise_for_status()` 变为异常。

## Fetch 验证门

每个 Page 默认配置一个 `VerificationGate`，其 checker 是 Cloudflare 响应识别器。没有注册
handler 时，命中验证页的 Fetch 不会无限循环，会直接返回当前 `FetchResult`。

需要在命中验证响应后刷新认证状态时，可显式配置：

```python
async def checker(response) -> bool:
    return response.status == 401

async def handler(context) -> None:
    page = context.page
    await page.goto("https://example.com/login")
    # 完成业务自己的登录或人工验证步骤。

page.fetch.verify_gate.configure(checker, handler, max_retries=1)
response = await page.fetch.get("https://example.com/api/account")
```

验证门会协调同一 Page 上并发的 fetch：第一个命中验证的请求执行 handler，其他请求等待后再决定
是否重发。handler 必须是有限时间、幂等或可重入的流程；不要在 handler 内无限等待验证码。
普通请求、性能测试或无需验证处理的调用可传 `check_fp=False`。

## Challenge / Fingerprint 能力

通用 challenge 逻辑位于 `base/fingerprint`，不依赖 Playwright。对外只使用页面对象上的
`solve_cloudflare()`，不要自行拼接 shadow、iframe、Target 或 Runtime 命令：

```python
passed = await page.solve_cloudflare(timeout=30, poll_interval=0.3, max_attempts=3)
if not passed:
    raise RuntimeError("Cloudflare challenge was not resolved")
```

`solve_cloudflare()` 会识别 challenge 标题或 Cloudflare iframe，并在每轮重新扫描外层 closed
Shadow DOM。跨域 iframe 成为 OOPIF 后，Playwright 通过 browser-level CDP
`Target.getTargets`/`Target.attachToTarget` 连接当前 iframe target，在子 target 中执行
`DOM.getDocument(depth=-1, pierce=True)`，定位内部 shadow root 的
`input[type="checkbox"]`，然后按 `DOM.scrollIntoViewIfNeeded`、`DOM.getBoxModel`、
`Input.dispatchMouseEvent(mouseMoved/mousePressed/mouseReleased)` 的顺序执行真实鼠标点击，
按下和释放之间保持短暂间隔。iframe 重渲染会使节点失效，因此每轮都会重新获取 iframe 和
checkbox。整个流程最多等待 `timeout` 秒；点击后若仍是 challenge（包括重定向到同类
challenge）会在剩余时间内继续下一轮，最多 `max_attempts` 轮。这样旧 iframe 重建时不会
为每次重试重复增加完整 timeout。只有 challenge 真正消失才返回 `True`，单独出现
`cf_clearance` cookie 不代表完成。点击后的旧标题/旧 iframe 状态只会进入最多约 5 秒的
收敛窗口；确认 clearance 已出现且 challenge iframe 消失后立即返回，不会等待外层剩余时间。

日志默认关闭。需要诊断时设置 `LJP_BROWSER_DEBUG_CDP=1`，只会输出 challenge 开始、发现
shadow/iframe、发现 checkbox、执行点击、解析失败和最终重试结果等关键事件，不会输出完整
Document、ShadowRoot 或 CDP 响应内容。

`CloudflareChallenge`、`CDPDOM` 和页面上的下划线方法是内部实现。其他后端可以复用
`base/fingerprint` 的 `ChallengePage`、`ChallengeTarget` 和 `ChallengeSolver`，但应为自己的
页面提供一个类似的单一公开入口，不要把内部 CDP 遍历方法暴露给业务代码。

这是辅助自动化能力，不是通用绕过保证。跨域 frame、站点重新渲染、交互式挑战、环境信誉与服务端
策略都可能让 `solve()` 返回 `False`。业务必须处理失败分支，并遵守目标站点授权和服务条款。

新增其他站点 profile 时：

1. 在 `base/fingerprint` 定义 `ChallengeTarget` 和基于 `ChallengeSolver` 的 profile，不导入具体浏览器。
2. 在具体后端子包创建绑定对象，例如 `playwright/fingerprint.py`。
3. 从该后端 Page 暴露明确的能力属性，并保持基础层不依赖具体后端。
4. 为 profile 的 detection、cookie 判定、CDP 命令和失败结果添加无网络单元测试。

## 同步基础包装器

`base.model.Browser`、`BrowserContext`、`Page` 是同步、后端可插拔的最小包装器。它们负责
生命周期、headers、cookies、导航和 evaluate；底层由 `SyncBrowserBackend` 实现。

```python
from ljp_page.request.browser import Browser, BrowserConfig

with Browser.playwright(BrowserConfig(browser_type="chromium", channel=None)) as browser:
    page = browser.new_page()
    result = page.goto("https://example.com")
    print(result.status, page.title())
```

同步基础包装器目前不承诺 `page.cdp`、`page.fetch` 或 `page.fingerprint`。这些能力属于异步
Playwright 的实现；为其他同步后端增加能力时，应先扩展明确的基础契约，而不是在同步 `Page`
中放入后端判断。

实现新同步后端时，满足 `SyncBrowserBackend` 协议，并让原生 browser/context/page 分别保存在
对应包装器的 `source`。不要修改 `Browser`、`BrowserContext`、`Page` 来识别后端类型。

## 测试与修改定位

| 需求 | 首先查看 |
| --- | --- |
| 异步 Browser/Context/Page 生命周期、headers、cookies | `playwright/browser.py`、`context.py`、`page.py` |
| Playwright 启动和 Context 配置 | `playwright/config.py` |
| CDP 高层操作或事件 | `playwright/cdp.py`、`base/model/async_api.py` |
| 页面内 Fetch、请求体、返回值 | `playwright/request.py`、`base/model/types.py` |
| 验证门并发逻辑 | `playwright/verification.py` |
| 通用 challenge/CDP DOM 行为 | `base/fingerprint/` |
| 同步后端契约和包装器 | `base/model/backend.py`、`browser.py` |
| 异步 Playwright 集成测试 | `tests/modules/request/bro/test_playwright_async.py` |
| fingerprint 无网络单元测试 | `tests/modules/request/bro/test_fingerprint.py` |
| 同步基础包装器测试 | `tests/modules/request/bro/test_sync_browser_model.py` |

修改公开方法、返回类型、配置字段、Cookie/Header 语义、CDP helper、fetch 参数、challenge
profile 或生命周期时，必须同步更新本文件和对应测试。测试命令：

```powershell
.\.venv\Scripts\python.exe -m pytest -q `
  tests\modules\request\bro\test_sync_browser_model.py `
  tests\modules\request\bro\test_fingerprint.py `
  tests\modules\request\bro\test_playwright_async.py
```

## AI 修改规则

- 优先使用本文记录的公共 API 和返回类型；无法满足时再读取对应源码。
- 新后端必须实现 `base` 契约，并且只在自己的子包内处理原生对象差异。
- 新的通用 CDP/challenge 能力放在 `base/fingerprint` 或明确的 `base` 抽象中；不要复制到每个后端。
- 新的 Playwright 专属能力放在 `playwright` 子包，通过包装对象或 `source` 暴露。
- 文档中的示例刻意使用 `source`、`page.cdp`、`page.fetch` 和 `page.fingerprint`；保持这一结构。
