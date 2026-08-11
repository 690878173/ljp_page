"""测试 ljp_page._module.file.manager —— SyncFileWriter 与 AsyncFileWriter。"""
from __future__ import annotations

import asyncio
import os
import tempfile
import threading
import time
from pathlib import Path

import pytest

from ljp_page.file import AsyncFileWriter, SyncFileWriter
from ljp_page.exc import LJPExc


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def count_files_in_dir(d: Path) -> int:
    return sum(1 for _ in d.iterdir() if _.is_file())


# ---------------------------------------------------------------------------
# SyncFileWriter
# ---------------------------------------------------------------------------

class TestSyncFileWriter:
    def test_start_stop_lifecycle(self):
        w = SyncFileWriter()
        assert not w._running

        w.start()
        assert w._running
        assert w._thread is not None
        assert w._thread.is_alive()

        w.stop(join=True)
        assert not w._running
        w._thread.join(timeout=2)
        assert not w._thread.is_alive()

    def test_start_twice_does_not_double_start(self):
        w = SyncFileWriter()
        w.start()
        tid = w._thread.ident
        w.start()  # second call should be noop
        assert w._thread.ident == tid
        w.stop()

    def test_stop_when_not_running(self):
        w = SyncFileWriter()
        w.stop()  # should not crash
        w.stop(join=True)

    def test_context_manager(self):
        with SyncFileWriter() as w:
            assert w._running
        assert not w._running

    def test_submit_writes_data(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "a.txt"

            with SyncFileWriter() as w:
                w.submit(path, "hello\n")
                w.submit(path, "world\n")
                # give the worker thread a moment
                time.sleep(0.3)

            assert path.exists()
            content = read_file(path)
            assert "hello" in content
            assert "world" in content

    def test_submit_multiple_files(self):
        with tempfile.TemporaryDirectory() as td:
            p1 = Path(td) / "one.txt"
            p2 = Path(td) / "two.txt"

            with SyncFileWriter() as w:
                w.submit(p1, "aaa\n")
                w.submit(p2, "bbb\n")
                time.sleep(0.3)

            assert read_file(p1) == "aaa\n"
            assert read_file(p2) == "bbb\n"

    def test_stop_drains_queue(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "drain.txt"
            w = SyncFileWriter()
            w.start()
            for i in range(50):
                w.submit(p, f"line {i}\n")
            w.stop(join=True)

            content = read_file(p)
            lines = content.strip().splitlines()
            assert len(lines) == 50

    def test_writes_to_absolute_and_relative_paths(self):
        with tempfile.TemporaryDirectory() as td:
            abs_path = Path(td) / "abs.txt"
            rel_path = Path("rel_test.txt")

            with SyncFileWriter() as w:
                w.submit(abs_path, "abs\n")
                w.submit(rel_path, "rel\n")
                time.sleep(0.3)

            assert read_file(abs_path) == "abs\n"

            # rel_path 被 resolve 到 cwd，清理
            resolved = rel_path.resolve()
            try:
                assert read_file(resolved) == "rel\n"
            finally:
                resolved.unlink(missing_ok=True)

    def test_lru_eviction(self):
        """当打开文件数超过 max_open_files 时，LRU 淘汰最久未用的文件。"""
        with tempfile.TemporaryDirectory() as td:
            # max_open_files=2, idle_timeout=0 以便立即淘汰
            w = SyncFileWriter(max_open_files=2, idle_timeout=0)
            w.start()

            paths = [Path(td) / f"f{i}.txt" for i in range(5)]
            for p in paths:
                w.submit(p, p.name + "\n")

            # 给 worker 一些时间淘汰
            time.sleep(0.5)
            w.stop()

            # 每个文件都应该存在且内容完整
            for p in paths:
                assert p.exists(), f"{p.name} should exist"
                assert read_file(p) == p.name + "\n"

    def test_submit_creates_parent_dirs(self):
        with tempfile.TemporaryDirectory() as td:
            nested = Path(td) / "deep" / "nested" / "file.txt"
            with SyncFileWriter() as w:
                w.submit(nested, "deep\n")
                time.sleep(0.3)
            assert nested.exists()
            assert read_file(nested) == "deep\n"

    def test_atomic_append(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "append.txt"
            with SyncFileWriter() as w:
                w.submit(p, "first\n")
                w.submit(p, "second\n")
                w.submit(p, "third\n")
                time.sleep(0.3)
            assert read_file(p) == "first\nsecond\nthird\n"

    def test_submit_from_multiple_threads(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "mt.txt"

            def producer(start: int, count: int):
                for i in range(start, start + count):
                    w.submit(p, f"{i}\n")

            w = SyncFileWriter()
            w.start()

            threads = [
                threading.Thread(target=producer, args=(0, 25)),
                threading.Thread(target=producer, args=(25, 25)),
                threading.Thread(target=producer, args=(50, 25)),
                threading.Thread(target=producer, args=(75, 25)),
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            w.stop(join=True)

            lines = read_file(p).strip().splitlines()
            assert len(lines) == 100

    def test_file_map_cleared_on_stop(self):
        w = SyncFileWriter()
        w.start()
        with tempfile.TemporaryDirectory() as td:
            w.submit(Path(td) / "x.txt", "x\n")
            time.sleep(0.3)
            w.stop(join=True)
            assert len(w._file_map) == 0
            assert w._lru_list.size == 0


# ---------------------------------------------------------------------------
# AsyncFileWriter
# ---------------------------------------------------------------------------

class TestAsyncFileWriter:
    @pytest.mark.asyncio
    async def test_start_stop_lifecycle(self):
        w = AsyncFileWriter()
        assert not w._running

        w.start()
        assert w._running
        assert w._task is not None
        assert not w._task.done()

        await w.stop()
        assert not w._running

    @pytest.mark.asyncio
    async def test_start_twice_does_not_double_start(self):
        w = AsyncFileWriter()
        w.start()
        w.start()  # should be noop
        assert w._running
        await w.stop()

    @pytest.mark.asyncio
    async def test_stop_when_not_running(self):
        w = AsyncFileWriter()
        await w.stop()  # should not crash

    @pytest.mark.asyncio
    async def test_submit_writes_data(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "a.txt"
            w = AsyncFileWriter()
            w.start()
            await w.submit(p, "hello\n")
            await w.submit(p, "world\n")
            await w.stop()

            assert read_file(p) == "hello\nworld\n"

    @pytest.mark.asyncio
    async def test_submit_multiple_files(self):
        with tempfile.TemporaryDirectory() as td:
            p1 = Path(td) / "one.txt"
            p2 = Path(td) / "two.txt"
            w = AsyncFileWriter()
            w.start()
            await w.submit(p1, "aaa\n")
            await w.submit(p2, "bbb\n")
            await w.stop()

            assert read_file(p1) == "aaa\n"
            assert read_file(p2) == "bbb\n"

    @pytest.mark.asyncio
    async def test_submit_before_start_raises(self):
        w = AsyncFileWriter()
        with pytest.raises(RuntimeError, match="未start"):
            await w.submit("dummy.txt", "data")

    @pytest.mark.asyncio
    async def test_stop_drains_queue(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "drain.txt"
            w = AsyncFileWriter()
            w.start()
            for i in range(50):
                await w.submit(p, f"line {i}\n")
            await w.stop()

            content = read_file(p)
            lines = content.strip().splitlines()
            assert len(lines) == 50

    @pytest.mark.asyncio
    async def test_lru_eviction(self):
        with tempfile.TemporaryDirectory() as td:
            w = AsyncFileWriter(max_open_files=2, idle_timeout=0)
            w.start()

            paths = [Path(td) / f"f{i}.txt" for i in range(5)]
            for p in paths:
                await w.submit(p, p.name + "\n")

            await w.stop()

            for p in paths:
                assert p.exists(), f"{p.name} should exist"
                assert read_file(p) == p.name + "\n"

    @pytest.mark.asyncio
    async def test_atomic_append(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "append.txt"
            w = AsyncFileWriter()
            w.start()
            await w.submit(p, "first\n")
            await w.submit(p, "second\n")
            await w.submit(p, "third\n")
            await w.stop()

            assert read_file(p) == "first\nsecond\nthird\n"

    @pytest.mark.asyncio
    async def test_concurrent_submit(self):
        """多个协程同时 submit 到同一个写入器。"""
        with tempfile.TemporaryDirectory() as td:
            exc = LJPExc()
            p = Path(td) / "concurrent.txt"
            w = AsyncFileWriter()
            w.start()

            async def batch(start: int, count: int):
                for i in range(start, start + count):
                    await w.submit(p, f"{i}\n")

            ls = exc.submit_many([
                batch(0, 30),
                batch(30, 30),
                batch(60, 40)],mode='async'
            )
            for i in ls:
                await i
            await w.stop()
            exc.shutdown()
            lines = read_file(p).strip().splitlines()
            assert len(lines) == 100

    @pytest.mark.asyncio
    async def test_large_write(self):
        """提交较大数据量。"""
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "large.txt"
            w = AsyncFileWriter()
            w.start()
            num = 10000
            big_line = "x" * num + "\n"
            for _ in range(100):
                await w.submit(p, big_line)

            await w.stop()

            content = read_file(p)
            assert len(content) == 100 * (num + 1)

    @pytest.mark.asyncio
    async def test_file_map_cleared_on_stop(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "cleanup.txt"
            w = AsyncFileWriter()
            w.start()
            await w.submit(p, "data\n")
            await w.stop()

            assert len(w._file_map) == 0
            assert w._lru_list.size == 0
