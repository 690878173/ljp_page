import asyncio
from ljp_page._module.tools.bind import coerce_bind_task

class FP:
    """反扒闸门：保证同一轮反扒只由一个请求执行状态更新。"""

    def __init__(self):
        self._refresh_lock = asyncio.Lock()
        self._ready = asyncio.Event()
        self._ready.set()
        self._version_event = asyncio.Event()
        self._version_event.set()
        self._version = 0



        self.fp_ok = False

    async def before_request(self) -> int:
        """请求前调用；若正在更新状态，则等待更新完成。"""
        await self._version_event.wait()
        self._version_event.clear()
        self._version_event.set()
        return self._version

    async def handle_blocked(self, seen_version: int,refresh_f,*args,**kwargs) -> None:
        self.fp_ok = False
        await self._ready.wait()
        """发现反扒后调用；同一轮只允许一个请求执行更新。"""
        if self._version != seen_version:
            return


        async with self._refresh_lock:
            if self._version != seen_version:
                return
            if self.fp_ok:
                return

            self._ready.clear()
            try:
                await coerce_bind_task(refresh_f, *args, **kwargs).create_awaitable()
                self._version += 1
            finally:
                self._ready.set()
                self.fp_ok = True


if __name__ == '__main__':
    from ljp_page.async_ import LJPExc


    async def t2(i):
        for j in range(10 - i):
            print(f't2第{j}更新:{i}')
            await asyncio.sleep(1)


    async def t1(i):
        num_id = await fp.before_request()
        await asyncio.sleep(2)
        res = await fp.handle_blocked(num_id, t2, num_id)
        print(res)

        return i


    async def main():
        ls = [t1(i) for i in range(10)]
        res_ls = []
        for i in ls:
            await asyncio.sleep(0.1)
            s = exc.submit_inside(i)
            res_ls.append(s)
        ls = [t1(i) for i in range(10)]
        for i in ls:
            await asyncio.sleep(0.1)
            s = exc.submit_inside(i)
            res_ls.append(s)
        for i in res_ls:
            res = await i


    exc = LJPExc()
    fp = FP()

    s = exc.submit(main())
    s.result()

    exc.shutdown()


__all__ = ["FP"]
