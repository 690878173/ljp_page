# Runtime AI Context

## 入口与目标

公开调度入口是 `LJPExc`，位于 `ljp_page._module.runtime.exc`。它把同步函数、
协程函数和已创建的协程统一提交，返回项目的 `Task[T]` 句柄。

`Task` 是调用方唯一应依赖的结果句柄：同步代码用 `result()`，异步代码用
`await task` 或 `await task.wait_async()`。不要把底层 `Future` 当作业务 API。

## 常用方式

```python
from ljp_page._module.runtime import LJPExc

with LJPExc(sem1_concurrent=20, sem2_concurrent=100) as exc:
    task = exc.submit(work, "input", mode="auto")
    value = task.result()
```

```python
async def run(exc: LJPExc) -> str:
    task = exc.submit(fetch, "https://example.com")
    return await task
```

使用 `submit_many()` 批量提交。需要预先绑定参数时用 `bind()`；批量元组格式为
`(target, args_tuple, kwargs_dict)`。

## API 速查

| API | 输入 | 输出/用途 |
| --- | --- | --- |
| `submit(target, *args, mode="auto", ...)` | 函数、协程函数或协程对象 | 一个 `Task[T]` |
| `submit_inside(...)` | 与 `submit` 相同 | 默认使用 `sem2` 的 `Task[T]` |
| `submit_many(tasks, ...)` | 多个目标或三元组任务 | `list[Task[T]]` |
| `bind(target, *args, **kwargs)` | 预绑定目标与参数 | 可再次传给 `submit` 的 `BindTask` |
| `cancel(task_id)` / `cancel_all()` | 单个 ID / 全部活动任务 | 取消结果数量或布尔值 |
| `get_task_handle(task_id)` | 任务 ID | `Task` 或 `None` |
| `get_task_status(task_id)` | 任务 ID | `pending`、`running`、`done`、`failed`、`cancelled`、`not_found` |
| `get_stats()` | 无 | total/running/success/failed/cancelled 统计快照 |
| `shutdown(...)` | `wait`、`cancel_futures`、`async_timeout` | 关闭已创建的后端资源 |

`Task` 可读取 `task_id`、`target_name`、`mode_requested`、`mode_resolved`、`backend_name`、
`semaphore_names` 和 `status`。`add_done_callback()` 接收的是当前 `Task`，不是底层 Future。

## 调度与限流

- `mode="auto"`：协程目标走 async；在运行中的事件循环内提交普通函数走 thread；其他普通函数走 sync。
- 可显式指定 `sync`、`async`、`thread`；`process` 目前只是预留接口。
- `submit()` / `submit_many()` 默认使用命名信号量 `sem1`；`submit_inside()` /
  `submit_many_inside()` 默认使用 `sem2`。调用时可传 `semaphore` 或 `semaphores` 覆盖。
- 不要在正在运行的事件循环中，对未完成的 `Task` 调用阻塞式 `result()` 或 `exception()`。

## 调用约束与常见错误

- 将协程对象直接传给 `submit` 后，不要再自行 await 同一个协程对象。
- `mode="thread"` 只用于普通函数；协程应使用 `async` 或 `auto`。
- `timeout` 是调度层参数，当前仅 async 后端会用于包装协程；它不等同于 HTTP 请求超时，
  HTTP 超时由 Session 配置管理。
- 在 `async def` 内等待调度结果，使用 `await task`，不要循环调用 `task.result()`。
- `submit_many()` 只负责调度和返回句柄，不会自动吞掉目标函数异常；异常在 `result()` / `await` 时体现。
- 任务需要共享限流时传同一个命名信号量或同一个 `asyncio.Semaphore`，不要在每个任务内新建信号量。

## 生命周期与边界

- `LJPExc` 按需创建线程池和后台异步运行时；使用结束必须调用 `shutdown()`，推荐 `with` 管理。
- `cancel()` 接受任务 ID；`cancel_all()` 取消所有活动任务；可用 `get_stats()` 和任务 ID 查询接口观察状态。
- runtime 使用 `ljp_page.logger.logger` 作为唯一默认日志入口，不接受也不转发 logger 参数。
- 业务代码不应直接管理 `Async`、`ThreadPool` 或 BackendRouter，除非正在维护 runtime 自身。

## 修改定位

| 需求 | 首先查看 |
| --- | --- |
| 对外调度 API、信号量、关闭 | `exc.py` |
| `Task` 等待、状态、回调行为 | `task.py` |
| ID、历史记录、统计和取消 | `registry.py` |
| auto 模式选择或后端生命周期 | `backends/router.py` |
| 后台事件循环或线程池实现 | `backends/ljp_async.py`、`backends/ljp_threadpool.py` |

先保持 `LJPExc -> Router -> Backend -> Task` 的职责方向；不要让业务层直接绑定某个 Backend。

## 修改时同步

修改 `LJPExc`、`Task`、调度模式、默认信号量、关闭语义或日志边界时，更新本文件。
