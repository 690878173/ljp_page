# pydoll 模块用法指南

## 引言

`pydoll` 是当前项目中用于浏览器自动化的核心子模块，位于 `ljp_page/_modules/pydoll`。它以 Chrome DevTools Protocol（CDP）为基础，围绕 Chromium 内核浏览器提供了页面导航、元素定位、键鼠交互、浏览器内请求、网络事件监听、下载处理、结构化数据提取等能力。

结合当前项目结构，实际使用时建议优先走项目已经提供好的封装入口，而不是直接从 vendored 目录手写长路径导入。这样做有两个好处：一是导入路径更短，二是后续如果项目调整内部结构，业务代码的改动面会更小。

## 一、模块定位与推荐导入方式

### 1.1 推荐导入

当前项目已经对 `Edge` 和 `ChromiumOptions` 做了轻量封装，推荐写法如下：

```python
import asyncio

from ljp_page.pc.edge import Pydoll_Edge as Edge
from ljp_page.pc.edge import Pydoll_ChromiumOptions as ChromiumOptions
```

如果你希望直接使用内部模块，也可以这样导入：

```python
from ljp_page._modules.pydoll.browser import Chrome, Edge
from ljp_page._modules.pydoll.browser.options import ChromiumOptions
from ljp_page._modules.pydoll.constants import By, Key, PageLoadState
```

### 1.2 当前模块的运行特点

这个模块有三个非常重要的使用习惯，初次上手时最容易忽略：

1. 它是异步 API，必须放在 `async def` 中运行，并通过 `asyncio.run()` 启动。
2. `async with Edge(...) as browser` 只负责资源清理，不会自动帮你启动浏览器；真正启动浏览器要手动执行 `await browser.start()`。
3. 模块里既有普通属性，也有“异步属性”。异步属性的写法是 `await 对象.属性`，不是 `await 对象.属性()`。

### 1.3 关键对象总览

| 字段名称 | 数据类型 | 核心含义 | 备注 |
| --- | --- | --- | --- |
| `Pydoll_Edge` / `Edge` | 浏览器类 | 基于 Edge 的 CDP 自动化入口 | Windows 下通常优先使用 |
| `Chrome` | 浏览器类 | 基于 Chrome 的 CDP 自动化入口 | 需能定位到 Chrome 可执行文件 |
| `ChromiumOptions` | 配置类 | 浏览器启动参数、首选项、加载策略配置 | 与 `Edge`、`Chrome` 配合使用 |
| `Browser` | 抽象基类 | 浏览器生命周期、标签页、上下文、Cookie、权限管理 | 一般不直接实例化 |
| `Tab` | 页面对象 | 页面导航、脚本执行、事件监听、网络日志、下载控制 | 自动化主战场 |
| `WebElement` | 元素对象 | 点击、输入、截图、Shadow DOM、脚本执行 | 由 `tab.query()` 或 `tab.find()` 返回 |
| `Request` | 请求对象 | 使用浏览器上下文发起 HTTP 请求 | 自动携带浏览器 Cookie 与会话状态 |
| `Response` | 响应对象 | 浏览器内请求的响应包装 | 提供 `status_code`、`text`、`json()` 等 |
| `ExtractionModel` | 模型基类 | 结构化抽取模型定义 | 基于 `pydantic` |
| `Field` | 字段描述函数 | 描述提取规则、属性名与转换逻辑 | 与 `ExtractionModel` 配套使用 |

### 1.4 异步属性与普通属性的区别

下面这张表很关键，能避免大量无意义报错。

| 字段名称 | 数据类型 | 核心含义 | 正确写法 |
| --- | --- | --- | --- |
| `tab.title` | 异步属性 | 当前页面标题 | `title = await tab.title` |
| `tab.current_url` | 异步属性 | 当前页面 URL | `url = await tab.current_url` |
| `tab.page_source` | 异步属性 | 当前页面 HTML | `html = await tab.page_source` |
| `element.text` | 异步属性 | 元素文本 | `text = await element.text` |
| `element.inner_html` | 异步属性 | 元素 HTML | `html = await element.inner_html` |
| `element.bounds` | 异步属性 | 元素边界坐标 | `bounds = await element.bounds` |
| `tab.request` | 普通属性 | 浏览器内请求助手 | `resp = await tab.request.get(...)` |
| `tab.keyboard` | 普通属性 | 页面级键盘控制器 | `await tab.keyboard.press(...)` |
| `tab.mouse` | 普通属性 | 页面级鼠标控制器 | `await tab.mouse.click(...)` |
| `tab.scroll` | 普通属性 | 页面级滚动控制器 | `await tab.scroll.to_bottom()` |
| `element.attributes` | 普通属性 | 元素已缓存属性 | `attrs = element.attributes` |

## 二、基础启动方式

### 2.1 最小可运行示例

这是当前项目里最推荐的起步方式：

```python
import asyncio

from ljp_page.pc.edge import Pydoll_Edge as Edge
from ljp_page.pc.edge import Pydoll_ChromiumOptions as ChromiumOptions


async def main():
    options = ChromiumOptions()
    options.headless = True

    async with Edge(options=options) as browser:
        # 注意：进入上下文后仍然需要显式启动浏览器
        tab = await browser.start()

        await tab.go_to("https://example.com")

        # title 是异步属性，不是方法
        title = await tab.title
        print(title)


asyncio.run(main())
```

### 2.2 Windows 环境下的浏览器路径

当前模块会在 Windows 下自动尝试定位以下浏览器：

| 字段名称 | 数据类型 | 核心含义 | 取值范围 |
| --- | --- | --- | --- |
| `Edge` 默认路径 | `str` | 自动查找 Edge 可执行文件 | `C:\Program Files\Microsoft\Edge\Application\msedge.exe` 等 |
| `Chrome` 默认路径 | `str` | 自动查找 Chrome 可执行文件 | `C:\Program Files\Google\Chrome\Application\chrome.exe` 等 |
| `options.binary_location` | `str` | 手动指定浏览器路径 | 建议填绝对路径 |

当自动定位失败时，手动指定即可：

```python
options = ChromiumOptions()
options.binary_location = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
```

### 2.3 连接已有浏览器

如果浏览器已经以远程调试模式启动，可以直接连接 WebSocket 地址：

```python
async with Edge() as browser:
    tab = await browser.connect("ws://127.0.0.1:9222/devtools/browser/xxx")
    print(await tab.title)
```

这个用法适合接管已启动的浏览器环境，但前提是你已经拿到了可用的 CDP WebSocket 地址。

## 三、浏览器配置 `ChromiumOptions`

### 3.1 常用配置项

`ChromiumOptions` 既可以控制命令行参数，也可以控制浏览器首选项。

| 字段名称 | 数据类型 | 核心含义 | 备注 |
| --- | --- | --- | --- |
| `headless` | `bool` | 是否无头启动 | 设为 `True` 会自动附加 `--headless` |
| `binary_location` | `str` | 浏览器可执行文件路径 | 自动识别失败时手动指定 |
| `start_timeout` | `int` | 浏览器启动验证超时时间 | 单位为秒 |
| `page_load_state` | `PageLoadState` | 页面加载等待策略 | 推荐 `INTERACTIVE` 或 `COMPLETE` |
| `browser_preferences` | `dict` | Chromium 首选项配置集合 | 底层会合并写入 |
| `webrtc_leak_protection` | `bool` | 是否开启 WebRTC 泄漏保护 | 开启时自动加启动参数 |
| `arguments` | `list[str]` | 当前命令行参数列表 | 可查看最终参数状态 |

### 3.2 常用方法与偏好设置

| 字段名称 | 数据类型 | 核心含义 | 备注 |
| --- | --- | --- | --- |
| `add_argument()` | 方法 | 追加浏览器启动参数 | 例如代理、禁用沙箱等 |
| `remove_argument()` | 方法 | 删除指定启动参数 | 删除不存在参数会抛异常 |
| `set_default_download_directory()` | 方法 | 设置默认下载目录 | 对下载类场景很重要 |
| `set_accept_languages()` | 方法 | 设置浏览器语言头 | 例如 `zh-CN,zh,en-US,en` |
| `block_popups` | `bool` | 是否屏蔽弹窗 | 通过 Chromium 首选项实现 |
| `block_notifications` | `bool` | 是否屏蔽通知 | 适合减少站点干扰 |
| `allow_automatic_downloads` | `bool` | 是否允许自动下载 | 批量下载时常用 |
| `password_manager_enabled` | `bool` | 是否启用密码管理器 | 自动化时常设为 `False` |
| `open_pdf_externally` | `bool` | 是否外部打开 PDF | 可避免内嵌 PDF 干扰 |
| `prompt_for_download` | `bool` | 下载前是否弹确认框 | 自动化一般设为 `False` |

### 3.3 配置示例

```python
from ljp_page.pc.edge import Pydoll_ChromiumOptions as ChromiumOptions
from ljp_page._modules.pydoll.constants import PageLoadState

options = ChromiumOptions()
options.headless = True
options.page_load_state = PageLoadState.COMPLETE
options.set_default_download_directory(r"J:\ljp_package\downloads")
options.set_accept_languages("zh-CN,zh,en-US,en")
options.block_popups = True
options.block_notifications = True
options.allow_automatic_downloads = True
options.webrtc_leak_protection = True
options.add_argument("--window-size=1440,900")
```

### 3.4 关于 `page_load_state` 的建议

源码里定义了 `LOADING`、`INTERACTIVE`、`COMPLETE` 三个枚举值，但当前页面等待逻辑实际可靠覆盖的是 `INTERACTIVE` 与 `COMPLETE`。因此，在现阶段的项目代码里，建议优先使用以下两种：

1. `PageLoadState.INTERACTIVE`
2. `PageLoadState.COMPLETE`

## 四、浏览器与标签页管理

### 4.1 基础生命周期

`Browser` 侧最常用的方法如下：

| 字段名称 | 数据类型 | 核心含义 | 备注 |
| --- | --- | --- | --- |
| `start()` | 方法 | 启动浏览器并返回首个 `Tab` | 最常用入口 |
| `stop()` | 方法 | 关闭浏览器进程 | 正常结束时通常由上下文自动调用 |
| `new_tab()` | 方法 | 新建标签页 | 可直接传初始 URL |
| `get_opened_tabs()` | 方法 | 获取当前已打开标签页列表 | 多标签调度时使用 |
| `create_browser_context()` | 方法 | 创建隔离上下文 | 相当于独立会话空间 |
| `delete_browser_context()` | 方法 | 删除指定上下文 | 会连带关闭其标签页 |
| `get_cookies()` / `set_cookies()` | 方法 | 浏览器级 Cookie 读写 | 也可指定上下文 |

### 4.2 新建标签页与上下文示例

```python
async with Edge(options=options) as browser:
    tab = await browser.start()

    ctx_id = await browser.create_browser_context()
    tab2 = await browser.new_tab("https://example.com", browser_context_id=ctx_id)

    print(await tab.title)
    print(await tab2.title)
```

如果你需要多账号、多会话并行，这个“浏览器上下文”能力非常实用。它比在同一个标签页里频繁清 Cookie 更稳，也更符合浏览器原生机制。

## 五、页面对象 `Tab` 的核心能力

### 5.1 页面导航与页面信息

最常用的页面级方法如下：

| 字段名称 | 数据类型 | 核心含义 | 备注 |
| --- | --- | --- | --- |
| `go_to(url)` | 方法 | 导航到指定 URL | 会等待页面达到设定加载状态 |
| `refresh()` | 方法 | 刷新当前页面 | 可选绕过缓存 |
| `bring_to_front()` | 方法 | 将标签页置前 | 多标签调试时有用 |
| `close()` | 方法 | 关闭当前标签页 | 关闭后当前 `Tab` 不再可用 |
| `title` | 异步属性 | 当前页面标题 | 写法是 `await tab.title` |
| `current_url` | 异步属性 | 当前页面 URL | 写法是 `await tab.current_url` |
| `page_source` | 异步属性 | 当前页面完整 HTML | 写法是 `await tab.page_source` |

示例：

```python
await tab.go_to("https://example.com")

title = await tab.title
url = await tab.current_url
html = await tab.page_source

print(title)
print(url)
print(html[:300])
```

### 5.2 元素定位：`query()` 与 `find()`

这两个接口是页面自动化的核心。

**`query()` 的定位思路**

`query()` 接收原始 CSS 选择器或 XPath 表达式，更适合你已经知道页面结构的场景。

```python
button = await tab.query("#submit-btn")
rows = await tab.query("table tbody tr", find_all=True)
title = await tab.query("//h1", timeout=10)
```

**`find()` 的定位思路**

`find()` 更偏“条件式定位”，适合按 `id`、`class_name`、`name`、`tag_name`、`text` 或其他属性组合查找。

```python
username_input = await tab.find(name="username")
submit_button = await tab.find(tag_name="button", text="登录")
cards = await tab.find(class_name="card-item", find_all=True, raise_exc=False)
```

**`query()` 与 `find()` 的参数特点**

| 字段名称 | 数据类型 | 核心含义 | 备注 |
| --- | --- | --- | --- |
| `timeout` | `int` | 等待元素出现的秒数 | `0` 表示不等待 |
| `find_all` | `bool` | 是否返回多个元素 | `True` 时返回列表 |
| `raise_exc` | `bool` | 未找到时是否抛异常 | `False` 时便于自行判断 |

更通俗地说：

1. 页面结构稳定、选择器明确时，用 `query()` 更直接。
2. 更希望按属性组合“描述性查找”时，用 `find()` 更顺手。
3. 想做兜底判断时，把 `raise_exc=False` 打开，再根据返回结果分支处理。

### 5.3 元素对象 `WebElement`

元素定位成功后会得到 `WebElement`。它提供的能力已经足够覆盖大多数页面操作。

| 字段名称 | 数据类型 | 核心含义 | 备注 |
| --- | --- | --- | --- |
| `click()` | 方法 | 点击元素 | 支持 `humanize=True` |
| `click_using_js()` | 方法 | 使用 JS 触发点击 | 某些遮挡场景可兜底 |
| `clear()` | 方法 | 清空输入框 | 适用于输入框、文本域、可编辑区域 |
| `insert_text()` | 方法 | 用 JS 插入文本 | 更偏“直接写值” |
| `type_text()` | 方法 | 模拟逐字输入 | 可启用拟人输入 |
| `set_input_files()` | 方法 | 给文件输入框设置文件 | 适用于 `<input type="file">` |
| `wait_until()` | 方法 | 等待元素可见或可交互 | 常用于点击前同步 |
| `is_visible()` | 方法 | 判断元素是否可见 | 返回 `bool` |
| `is_interactable()` | 方法 | 判断元素是否可交互 | 返回 `bool` |
| `execute_script()` | 方法 | 在元素上下文执行 JS | `this` 指向当前元素 |
| `take_screenshot()` | 方法 | 截取元素截图 | 可文件保存或转 base64 |
| `get_shadow_root()` | 方法 | 获取 ShadowRoot | Shadow DOM 页面必备 |
| `text` | 异步属性 | 元素文本 | 写法是 `await element.text` |
| `inner_html` | 异步属性 | 元素 HTML | 写法是 `await element.inner_html` |

### 5.4 常见交互示例

```python
username = await tab.query("#username", timeout=10)
password = await tab.query("#password", timeout=10)
submit = await tab.query("button[type='submit']", timeout=10)

await username.clear()
await username.type_text("demo_user", humanize=True)

await password.clear()
await password.insert_text("123456")

await submit.wait_until(is_visible=True, is_interactable=True, timeout=10)
await submit.click()
```

这里有一个经验判断：

1. 如果目标站点对输入行为不敏感，用 `insert_text()` 会更快。
2. 如果站点前端框架依赖真实输入事件链，用 `type_text()` 更稳。
3. 如果页面容易出现遮挡、浮层、滚动位置不对等问题，先 `wait_until()` 再点击，成功率通常更高。

### 5.5 页面级键盘、鼠标、滚动控制

除了元素对象，`Tab` 还直接提供页面级输入控制器：

```python
from ljp_page._modules.pydoll.constants import Key

await tab.keyboard.press(Key.ENTER)
await tab.keyboard.hotkey(Key.CONTROL, Key.L)

await tab.scroll.to_bottom()
await tab.scroll.to_top(smooth=False)
```

这组 API 更适合做全局快捷键、页面滚动、画布点击、复杂输入轨迹这类元素级操作不够方便的场景。

## 六、JavaScript 执行

### 6.1 在页面级执行脚本

`tab.execute_script()` 直接在页面上下文执行 JavaScript。它返回的是底层 CDP 响应，而不是自动拆好的 Python 值。

```python
result = await tab.execute_script(
    "document.title",
    return_by_value=True,
)

title = result["result"]["result"]["value"]
print(title)
```

如果你只是想要标题、URL、HTML，优先使用已经封装好的异步属性更省事。

### 6.2 在元素级执行脚本

`element.execute_script()` 里的 `this` 会指向当前元素，因此写 DOM 操作尤其顺手：

```python
element = await tab.query("#target")

await element.execute_script(
    "this.style.border = '2px solid red';"
)

text_result = await element.execute_script(
    "return this.textContent.trim();",
    return_by_value=True,
)

text = text_result["result"]["result"]["value"]
print(text)
```

## 七、浏览器内请求能力

### 7.1 为什么用 `tab.request`

`tab.request` 的底层不是独立的 `requests` 会话，而是浏览器上下文里的 `fetch`。这意味着：

1. 它会自动复用当前浏览器 Cookie、登录态和会话环境。
2. 请求头里的浏览器默认信息会保留。
3. 它仍然处在浏览器安全模型里，CORS 规则也依然存在。

这使它特别适合“先登录页面，再调用页面内部 API”的场景。

### 7.2 常用请求方法

| 字段名称 | 数据类型 | 核心含义 | 备注 |
| --- | --- | --- | --- |
| `get()` | 方法 | 发起 GET 请求 | 支持 `params` |
| `post()` | 方法 | 发起 POST 请求 | 支持 `data` 与 `json` |
| `put()` | 方法 | 发起 PUT 请求 | 适合更新资源 |
| `patch()` | 方法 | 发起 PATCH 请求 | 适合部分更新 |
| `delete()` | 方法 | 发起 DELETE 请求 | 删除资源 |
| `head()` | 方法 | 发起 HEAD 请求 | 只关心响应头时使用 |
| `options()` | 方法 | 发起 OPTIONS 请求 | 适合预检或能力探测 |

### 7.3 请求示例

```python
response = await tab.request.get(
    "https://httpbin.org/get",
    params={"q": "pydoll"},
)

print(response.status_code)
print(response.ok)
print(response.url)
print(response.json())
```

### 7.4 带请求头的写法

注意，这里的 `headers` 不是字典，而是 `HeaderEntry` 风格的列表：

```python
response = await tab.request.post(
    "https://httpbin.org/post",
    json={"name": "ljp"},
    headers=[
        {"name": "X-Token", "value": "demo-token"},
        {"name": "X-Env", "value": "test"},
    ],
)
```

### 7.5 `Response` 对象怎么用

| 字段名称 | 数据类型 | 核心含义 | 备注 |
| --- | --- | --- | --- |
| `status_code` | `int` | HTTP 状态码 | 例如 `200`、`404` |
| `ok` | `bool` | 是否处于成功状态 | 200-399 为 `True` |
| `text` | `str` | 响应文本 | 文本场景最常用 |
| `content` | `bytes` | 原始字节内容 | 文件、图片等二进制场景使用 |
| `url` | `str` | 最终响应 URL | 发生重定向时尤其有用 |
| `headers` | `list[HeaderEntry]` | 响应头列表 | 不是 `dict` |
| `request_headers` | `list[HeaderEntry]` | 实际发出的请求头 | 可用于排查签名或鉴权问题 |
| `cookies` | `list[CookieParam]` | 本次响应设置的 Cookie | 新增或更新的 Cookie |
| `json()` | 方法 | 解析 JSON 响应 | 非 JSON 会抛异常 |
| `raise_for_status()` | 方法 | 对 4xx/5xx 抛异常 | 行为类似 `requests` |

如果你需要把响应头转成字典，建议手动转换：

```python
headers = {item["name"]: item["value"] for item in response.headers}
print(headers.get("content-type"))
```

### 7.6 HAR 录制

`tab.request.record()` 适合录制页面在某段操作期间的网络流量：

```python
from ljp_page._modules.pydoll.protocol.network.types import ResourceType

async with tab.request.record(
    resource_types=[ResourceType.FETCH, ResourceType.XHR]
) as capture:
    await tab.go_to("https://example.com")

capture.save("api_calls.har")
```

这类 HAR 文件特别适合做接口逆向、页面抓包归档或问题复现。

## 八、网络事件与请求拦截

### 8.1 监听网络日志

如果只是想看页面发出了什么请求，可以使用网络事件：

```python
await tab.enable_network_events()
await tab.go_to("https://example.com")

logs = await tab.get_network_logs()
for item in logs[:5]:
    print(item["params"]["request"]["url"])
```

### 8.2 拦截请求

如果你需要在请求发出前进行修改、阻断或伪造响应，就要用 Fetch 域事件。

核心步骤通常是：

1. `await tab.enable_fetch_events(...)`
2. 通过 `tab.on(...)` 监听 `Fetch.requestPaused`
3. 在回调里调用 `continue_request()`、`fail_request()` 或 `fulfill_request()`

示例：

```python
from ljp_page._modules.pydoll.protocol.fetch.events import FetchEvent
from ljp_page._modules.pydoll.protocol.network.types import ErrorReason


async def handle_request(event: dict):
    request_id = event["params"]["requestId"]
    url = event["params"]["request"]["url"]

    if "analytics" in url:
        await tab.fail_request(request_id, error_reason=ErrorReason.ABORTED)
        return

    await tab.continue_request(request_id)


await tab.enable_fetch_events()
callback_id = await tab.on(FetchEvent.REQUEST_PAUSED, handle_request)

await tab.go_to("https://example.com")

await tab.remove_callback(callback_id)
await tab.disable_fetch_events()
```

### 8.3 事件监听的使用方式

`tab.on(event_name, callback)` 和 `browser.on(event_name, callback)` 都支持注册 CDP 事件回调。常见事件枚举包括：

| 字段名称 | 数据类型 | 核心含义 | 典型用途 |
| --- | --- | --- | --- |
| `PageEvent` | 枚举 | 页面生命周期、对话框、文件选择器等事件 | 页面加载、弹窗、上传 |
| `NetworkEvent` | 枚举 | 请求与响应相关事件 | 网络日志、调试 |
| `FetchEvent` | 枚举 | 可拦截请求事件 | 请求拦截、改包 |
| `BrowserEvent` | 枚举 | 浏览器级事件 | 下载进度等 |

记住一点：注册回调之前，必须先启用对应域的事件能力，否则回调不会被触发。

## 九、下载、截图、PDF 与页面归档

### 9.1 页面截图

```python
await tab.take_screenshot(
    path="page.png",
    quality=100,
    beyond_viewport=True,
)
```

如果你不想落文件，也可以直接拿 base64：

```python
image_base64 = await tab.take_screenshot(as_base64=True)
```

### 9.2 元素截图

```python
card = await tab.query(".card")
await card.take_screenshot(path="card.png")
```

### 9.3 导出 PDF

```python
await tab.print_to_pdf(
    path="report.pdf",
    print_background=True,
    landscape=False,
)
```

### 9.4 离线保存整个页面资源

```python
await tab.save_bundle("page_bundle.zip")
await tab.save_bundle("page_inline.zip", inline_assets=True)
```

两种归档方式的区别在于：

1. `inline_assets=False` 时，资源以单独文件写入 ZIP。
2. `inline_assets=True` 时，资源会尽可能内联到 `index.html` 中。

### 9.5 下载监听

`expect_download()` 是一个异步上下文管理器，适合包住“会触发下载的动作”：

```python
async with tab.expect_download(
    keep_file_at=r"J:\ljp_package\downloads",
    timeout=60,
) as download:
    btn = await tab.query("#download-btn")
    await btn.click()

await download.wait_finished()
print(download.file_path)
```

`download` 句柄提供以下能力：

| 字段名称 | 数据类型 | 核心含义 | 备注 |
| --- | --- | --- | --- |
| `file_path` | `str | None` | 下载完成后的文件路径 | 需要成功触发下载后才可用 |
| `wait_started()` | 方法 | 等待下载开始 | 可单独监听起始时机 |
| `wait_finished()` | 方法 | 等待下载完成 | 最常用 |
| `read_bytes()` | 方法 | 读取下载文件字节 | 适合二进制处理 |
| `read_base64()` | 方法 | 读取下载文件 base64 | 适合二次传输 |

## 十、文件上传与文件选择器

### 10.1 直接给文件输入框赋值

如果页面上就是标准的 `<input type="file">`，最直接的方式是：

```python
file_input = await tab.query("input[type='file']")
await file_input.set_input_files(r"J:\ljp_package\data\demo.txt")
```

### 10.2 处理“点击按钮后弹文件选择器”的场景

如果页面不是直接暴露文件输入框，而是点击按钮后再弹出文件选择器，可使用 `expect_file_chooser()`：

```python
async with tab.expect_file_chooser(
    [r"J:\ljp_package\data\a.txt", r"J:\ljp_package\data\b.txt"]
):
    upload_btn = await tab.query("#upload-btn")
    await upload_btn.click()
```

这个上下文管理器的作用，是先监听文件选择器事件，再在事件触发时自动把文件路径灌进去。

## 十一、Shadow DOM 与 iframe

### 11.1 Shadow DOM

如果目标站点用了 Shadow DOM，可以用以下两种方式处理：

```python
host = await tab.query("my-component")
shadow_root = await host.get_shadow_root(timeout=10)
inner_button = await shadow_root.query("button")
await inner_button.click()
```

或者直接扫描整页 ShadowRoot：

```python
roots = await tab.find_shadow_roots(deep=True, timeout=10)
print(len(roots))
```

需要注意的是，ShadowRoot 场景下更适合使用 CSS 选择器，不建议继续使用 XPath。

### 11.2 iframe

模块里保留了 `get_frame()`，但源码已经标明它是废弃接口。当前更推荐的思路是直接围绕 iframe 元素本身或其 `iframe_context` 做处理，而不是继续把它当成一个完全独立的老式子页面对象去操作。

如果你只是在普通业务场景里做自动化，优先把注意力放在“先拿到 iframe 元素，再进入正确上下文”这个思路上即可。

## 十二、结构化数据提取

### 12.1 适合什么场景

当页面里存在相对稳定的数据结构，例如文章详情、商品卡片、列表项、作者信息、价格区域等，与其手动一个个 `query()` 再拼字典，不如直接定义抽取模型。这样代码更整齐，也更方便和后续数据处理逻辑对接。

### 12.2 基本写法

```python
from ljp_page._modules.pydoll.extractor.field import Field
from ljp_page._modules.pydoll.extractor.model import ExtractionModel


class ArticleInfo(ExtractionModel):
    title: str = Field(selector="h1")
    author: str | None = Field(selector=".author", default=None)
    read_count: int = Field(
        selector=".read-count",
        transform=lambda x: int(x.replace(",", "")),
    )
```

### 12.3 抽取单个对象

```python
data = await tab.extract(ArticleInfo)
print(data.model_dump())
```

### 12.4 在局部区域内抽取

如果页面有多个区域，而你只想在某个容器内做提取，可以用 `scope`：

```python
data = await tab.extract(
    ArticleInfo,
    scope=".article-detail",
    timeout=10,
)
```

### 12.5 批量抽取列表

```python
class ProductCard(ExtractionModel):
    name: str = Field(selector=".name")
    price: float = Field(selector=".price", transform=lambda x: float(x.replace("￥", "")))


items = await tab.extract_all(
    ProductCard,
    scope=".product-card",
    timeout=10,
    limit=20,
)

for item in items:
    print(item.model_dump())
```

### 12.6 `Field()` 的关键参数

| 字段名称 | 数据类型 | 核心含义 | 备注 |
| --- | --- | --- | --- |
| `selector` | `str | None` | CSS 或 XPath 选择器 | 最常用 |
| `attribute` | `str | None` | 不取文本，改取指定 HTML 属性 | 例如 `href`、`src` |
| `default` | 任意 | 提取失败时的默认值 | 字段非必填时常用 |
| `description` | `str | None` | 字段语义说明 | 可读性更强 |
| `transform` | 可调用对象 | 对原始文本做二次转换 | 常用于转数字、布尔、日期 |

举个属性抽取例子：

```python
class LinkInfo(ExtractionModel):
    title: str = Field(selector="a.title")
    url: str = Field(selector="a.title", attribute="href")
```

### 12.7 什么时候适合提取模型

你可以把判断标准记成一句话：当页面数据“结构清晰、字段稳定、后续要继续处理”时，就优先考虑 `extract()` 或 `extract_all()`。

## 十三、验证码、弹窗与特殊页面

### 13.1 JavaScript 弹窗

```python
await tab.enable_page_events()

if await tab.has_dialog():
    message = await tab.get_dialog_message()
    print(message)
    await tab.handle_dialog(accept=True)
```

### 13.2 Cloudflare Turnstile

模块内提供了两类能力：

1. `enable_auto_solve_cloudflare_captcha()`
2. `expect_and_bypass_cloudflare_captcha()`

典型写法如下：

```python
async with tab.expect_and_bypass_cloudflare_captcha(time_to_wait_captcha=8):
    await tab.go_to("https://目标站点")
```

这部分更适合作为专项能力使用，不建议一开始就默认开启，除非你已经明确知道目标站点使用了相关挑战页。

## 十四、常见异常与排查建议

| 字段名称 | 数据类型 | 核心含义 | 取值范围 | 备注 |
| --- | --- | --- | --- | --- |
| `FailedToStartBrowser` | 异常类 | 浏览器无法启动 | 路径错误、端口冲突、权限问题 | 先检查 `binary_location` 与浏览器安装情况 |
| `BrowserNotRunning` | 异常类 | 浏览器进程未运行 | 启动失败或已关闭 | 常见于重复关闭、异常中断后继续操作 |
| `ElementNotFound` | 异常类 | 元素未找到 | 选择器错误、页面未加载完 | 优先加 `timeout`，并检查实际 DOM |
| `WaitElementTimeout` | 异常类 | 等待元素超时 | 页面慢、懒加载、iframe/Shadow DOM | 先确认元素是否真的在当前上下文里 |
| `ElementNotInteractable` | 异常类 | 元素不可交互 | 被遮挡、未显示、禁用 | 可先 `wait_until()` 或改用 JS 兜底 |
| `NavigationError` | 异常类 | 页面导航失败 | DNS、证书、页面拒绝加载 | 看报错里的 `url` 与 `errorText` |
| `PageLoadTimeout` | 异常类 | 页面加载等待超时 | 页面极慢或加载策略过严 | 可考虑改 `page_load_state` 或增大超时 |
| `HTTPError` | 异常类 | 浏览器内请求失败 | 4xx、5xx 或请求流程异常 | 使用 `raise_for_status()` 或检查接口响应 |
| `DownloadTimeout` | 异常类 | 下载等待超时 | 链接未真正触发下载 | 先确认目标操作是否走浏览器下载链路 |
| `InvalidFileExtension` | 异常类 | 文件扩展名不受支持 | 截图、归档等输出路径不合规 | 检查保存路径后缀 |

## 结论与展望

就当前项目而言，`pydoll` 已经不是“简单点几下页面”的轻量封装，而是一套相当完整的异步浏览器自动化工具。它最适合的工作流通常是这样的：先通过 `Edge + ChromiumOptions` 启动浏览器，再围绕 `Tab` 完成导航、定位和交互，之后根据业务需要接入 `tab.request`、事件监听、下载处理，最后在数据型场景里通过 `ExtractionModel` 完成结构化提取。

如果只记三条最关键的使用规则，可以记住下面这三句：第一，所有操作都运行在异步上下文里；第二，`async with` 不等于自动启动，记得显式 `await browser.start()`；第三，像 `tab.title`、`tab.current_url`、`element.text` 这类值是“异步属性”，要写成 `await 对象.属性`。把这三件事掌握住，后面的 API 基本都能顺畅上手。
