# 统一任务调度层说明

## 引言

`ljp_page.runtime.ljp_exc` 提供一套精简后的统一调度入口，用来把同步函数、线程任务和协程任务收敛到同一套提交方式中。

当前版本只保留最核心的能力：

- `bind`
- `submit`
- `submit_inside`
- `submit_many`
- `submit_many_inside`
- `TaskHandle`

不再提供 `map`、`gather` 这类聚合接口，也不再保留旧命名参数兼容层。

## 核心对象

### BoundTask

`BoundTask` 用于绑定业务参数，避免和调度参数混在一起。

```python
task = exc.bind(fetch_user, user_id=1001)
handle = exc.submit(task, mode="thread")
```

### TaskHandle

`TaskHandle` 是统一返回值。无论底层任务来自同步执行、线程池还是异步运行时，对外都通过它来等待结果、查询状态和取消任务。

常用方法：

- `result(timeout=None)`
- `wait(timeout=None)`
- `wait_async()`
- `done()`
- `running()`
- `cancelled()`
- `cancel()`

## 对外接口

### submit

提交单个外层任务。

```python
handle = exc.submit(add, 1, 2, mode="sync", task_id="add-task")
print(handle.result())
```

### submit_inside

在异步任务内部继续派生子任务时使用，固定走内层并发控制。

```python
handle = exc.submit_inside(fetch_part, page=2, mode="async")
```

### submit_many

批量提交一组任务，返回 `list[TaskHandle]`。

支持两种输入形式：

1. `BoundTask`、普通函数、协程函数或 awaitable
2. `(target, args, kwargs)` 三元组

```python
handles = exc.submit_many(
    [
        exc.bind(add, 1, 2),
        (add, (3, 4), {}),
    ],
    mode="sync",
    task_id="batch",
)
```

### submit_many_inside

与 `submit_many` 相同，但固定走内层并发控制。

## 并发参数

`LJPExc` 只保留两项异步并发配置：

| 字段名称 | 含义 |
| --- | --- |
| `async_outer_concurrent` | 外层异步任务并发数 |
| `async_inner_concurrent` | 内层异步子任务并发数 |

示例：

```python
exc = LJPExc(
    async_outer_concurrent=10,
    async_inner_concurrent=50,
)
```

## 使用示例

### 单任务提交

```python
from ljp_page.runtime.ljp_exc import LJPExc

exc = LJPExc()

def add(a, b):
    return a + b

handle = exc.submit(add, 1, 2, mode="sync")
print(handle.result())
```

### 异步外层任务内部派生内层任务

```python
import asyncio

from ljp_page.runtime.ljp_exc import LJPExc

exc = LJPExc(async_outer_concurrent=2, async_inner_concurrent=20)

async def child(index):
    await asyncio.sleep(0.1)
    return index

async def parent():
    handles = exc.submit_many_inside(
        [exc.bind(child, index) for index in range(5)],
        mode="async",
        task_id="inner-batch",
    )
    return [await handle for handle in handles]

handle = exc.submit(parent, mode="async")
print(handle.result())
```
