# XS 小说采集框架上下文

## 入口

站点实现继承 `Xs`，业务只实现三个解析器：

```python
class SiteNovel(Xs):
    def parse_p1(self, html: str, url: str) -> P1Result: ...
    def parse_p2(self, html: str, url: str) -> P2Result: ...
    async def parse_p3(self, html: str, url: str) -> P3Item: ...
```

启动时可以传 ID 列表，也可以直接传一本小说 URL：

```python
collector = SiteNovel(config)
await collector.collect(ids=["57748", "57749"])
await collector.collect(url="https://www.bz444444444.com/57/57748/")
```

同步入口 `collector.run()` 会把完整采集协程提交到 `LJPExc`。不要在采集器内部再把
绑定当前事件循环的 `asyncio.Queue` 提交到 `LJPExc` 的异步后台 loop；生产者和消费者由
当前采集 loop 创建。`LJPExc` 负责外层生命周期、任务句柄和线程/异步运行时。

## 配置

`Config` 的关键字段：

| 字段 | 作用 |
| --- | --- |
| `base_url` | 浏览器首次验证和相对 URL 的根地址 |
| `p1_url` | ID 列表页模板；没有时输入直接视为详情 URL/ID |
| `p2_url` | 详情 URL 模板 |
| `p3_url` | 章节 URL 模板 |
| `id_list` | 默认输入 ID/URL 列表 |
| `browser_config` | Playwright 启动和 proxy 配置 |
| `session_config` | aiohttp/curl-cffi 的 headers、timeout、proxy、连接池配置 |
| `http_backend` | `aiohttp` 或 `curl_cffi` |
| `verify_timeout` / `verify_attempts` | 浏览器验证总预算和最多重试次数 |
| `image_dir` | 图片保存目录 |
| `max_workers` | 书籍生产者数量 |
| `chapter_concurrency` | 章节消费者数量 |

浏览器和 HTTP Session 必须使用同一出口 IP。配置浏览器 proxy 时，若
`session_config.Proxy` 没有显式配置，传输层会自动复制浏览器 proxy；显式配置时以
`session_config.Proxy` 为准。

## 传输层

`BrowserHttpTransport` 持有一个 Playwright 浏览器、一个验证页面和一个
`AsyncSessionPool`。初始化和请求流程如下：

1. 浏览器访问 bootstrap URL。
2. 调用 `page.solve_cloudflare()`。
3. 读取浏览器 cookies，并同步到 HTTP Session。
4. 通过 CDP 捕获浏览器导航和 Fetch 的真实 headers；过滤 `Host`、`Cookie`、
   `Content-Length` 和不兼容的 `Accept-Encoding`。
5. HTTP 请求遇到 Cloudflare challenge 时，重新使用同一个浏览器、同一个 proxy
   刷新验证，再同步 cookies/headers 后重试一次；若站点仍按连接指纹拒绝独立 HTTP，
   GET 请求最后回退到已验证页面的 Fetch，保证采集流程可继续。

`page.fetch` 只用于生成与浏览器一致的 Fetch 请求头和验证辅助；正文采集默认走
`AsyncSessionPool`，底层可选 aiohttp 或 curl-cffi。站点可能同时校验 TLS 指纹、IP、
cookies 和 headers，因此不能把 cookies 单独复制到另一个网络出口。

## 运行日志

所有运行日志统一使用：

```python
from ljp_page.logger import logger
```

采集过程中会记录列表页开始/完成、发现的小说数量、小说元数据开始/完成、章节开始/完成、
整本小说完成，以及 Cloudflare 验证开始、成功、失败和浏览器 Fetch 回退。日志不会使用
`print`，默认输出到控制台；并发任务的日志包含 URL 或小说标题，便于区分同时运行的任务。

## 生产者/消费者

`NovelPipeline` 有两级队列：

```text
输入 ids/URL
    -> 书籍生产者 -> 章节队列 -> 章节消费者 -> XsManager
```

书籍生产者全部结束后写入与消费者数量相同的 `_STOP` 哨兵。每个消费者消费一个哨兵后
退出并调用 `task_done()`。章节消费者共享每本书的 `XsManager`，管理器按章节 ID 缓冲并
顺序写入，因此网络完成顺序不会改变成书顺序。

## 文件与图片

每本书先写 `<title>.downloading.txt`，完成后导出 `<title>.txt` 并删除断点文件。中断时
保留下载文件，下次会从最后一个 `[CHAPTER_END]` 继续。

`BrowserHttpTransport.get_image()` 使用 URL 的 SHA-256 作为文件名，写入 `image_dir`，
同一 URL 重复请求不会重复写入。站点解析器只需调用 `await self.req.get_image(url)`；
OCR 或媒体处理属于站点层，不放进通用传输层。

## 扩展边界

- 新小说站点：继承 `Xs`，只实现 `parse_p1`、`parse_p2`、`parse_p3` 和必要的 `check_name`。
- 新媒体类型：复用 `BrowserHttpTransport`、`ImageStore` 和 `NovelPipeline` 的设计，
  新建独立的 `video` pipeline，不向 `XsManager` 添加视频分支。
- 不使用旧的 `RequestManager` 验证回调、`page.cf()`、`page.cdp_request`、多页面轮询或
  手工 `asyncio.sleep(10)` 重试。
