# 03-27-18-58-15
from __future__ import annotations

import asyncio

from ljp_page.runtime.ljp_exc import LJPExc


def add(a: int, b: int) -> int:
    """返回两个整数之和。"""
    return a + b


async def double(value: int) -> int:
    """异步返回输入值的两倍。"""
    await asyncio.sleep(0.01)
    return value * 2


def test_submit_and_submit_many_keep_minimal_api() -> None:
    exc = LJPExc()
    callback_task_ids: list[str] = []

    try:
        single_handle = exc.submit(add, 1, 2, mode="sync", task_id="single")
        assert single_handle.result() == 3

        handles = exc.submit_many(
            [
                exc.bind(add, 3, 4),
                (add, (5, 6), {}),
            ],
            mode="sync",
            task_id="batch",
            callback=lambda handle: callback_task_ids.append(handle.task_id),
        )

        assert [handle.result() for handle in handles] == [7, 11]
        assert [handle.task_id for handle in handles] == ["batch:1", "batch:2"]
        assert handles[0].target_name == "add"
        assert handles[0].bound_task is not None
        assert not hasattr(handles[0], "__dict__")
        assert callback_task_ids == ["batch:1", "batch:2"]
        assert not hasattr(exc, "map")
        assert not hasattr(exc, "gather")
        assert not hasattr(exc, "close")
        assert not hasattr(exc, "get_task_ids")
    finally:
        exc.shutdown()


def test_submit_many_inside_supports_nested_async_dispatch() -> None:
    exc = LJPExc(async_outer_concurrent=2, async_inner_concurrent=4)

    try:
        async def parent() -> list[int]:
            """在外层任务内部批量派生内层协程任务。"""
            handles = exc.submit_many_inside(
                [exc.bind(double, index) for index in range(4)],
                mode="async",
                task_id="inner-batch",
            )
            return [await handle for handle in handles]

        handle = exc.submit(parent, mode="async", task_id="outer-task")

        assert handle.result() == [0, 2, 4, 6]
        assert handle.mode_resolved == "async"
        assert exc.get_task_status("inner-batch:1") == "done"
        assert exc.get_task_status("inner-batch:4") == "done"
    finally:
        exc.shutdown()
