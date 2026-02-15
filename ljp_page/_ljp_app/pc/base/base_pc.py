import asyncio
import re
import time

import winsound
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple

from ...._ljp_network.requests import Requests
from ....async_ import Async
from ....threadpool import ThreadPool
from ....file import FileHandle
from ....file import Directory
from ....logger import Logger
from ...._ljp_core.base_class import Ljp_BaseClass,Ljp_Decorator
from ....exceptions import Notfound,No,MeetCheckError


class _mode:
    mode1 = 'mode1'
    mode2 = 'mode2'
    mode3 = 'mode3'
    book = 'book'
    video = 'video'

class _Base_Pc_init(Ljp_BaseClass):
    """异步爬虫基类，支持多种工作模式和运行时控制"""

    @dataclass
    class Config:
        """爬虫配置类"""
        base_url: str
        save_path: str
        p2_url: str
        threadpool_thread_num: int = 10
        max_workers: int = 5
        start_id: int = 1
        end_id: int = 5
        p1_url: Optional[str] = None
        id_ls: Optional[List[int]] = None
        proxy_list: Optional[List[str]] = None
        max_retries: int = 3
        timeout: float = 10
        cookies: Optional[Dict] = None
        headers: dict = None
        mode: str = 'mode1'
        worker_startup_delay: float = 1.0
        queue_get_timeout: float = 2.0
        session_close_timeout: float = 2.0

        def __post_init__(self):
            self._validate_base_params()
            self._validate_info_url()
            self._validate_save_path()
            self._validate_id_list()
            self._validate_mode_specific_params()

        def _validate_base_params(self) -> None:
            """验证基础参数"""
            if not self.base_url:
                raise ValueError("Config Error: base_url 不能为空")
            if not self.base_url.startswith('http'):
                raise ValueError(f"Config Error: base_url 格式错误 (必须以http/https开头): {self.base_url}")

        def _validate_info_url(self) -> None:
            """验证info_url参数"""
            if not self.p2_url:
                raise ValueError("Config Error: info_url 不能为空")
            if '{}' not in self.p2_url:
                raise ValueError(f"Config Error: info_url 必须包含 '{{}}' 占位符用于填充ID: {self.p2_url}")
            if not self.p2_url.startswith('http'):
                raise ValueError(f"Config Error: info_url 格式错误: {self.p2_url}")

        def _validate_save_path(self) -> None:
            """验证保存路径"""
            if not self.save_path:
                raise ValueError("Config Error: save_path 不能为空")

        def _validate_id_list(self) -> None:
            """验证并生成ID列表"""
            if self.id_ls is None:
                if self.start_id > self.end_id:
                    raise ValueError(f"Config Error: start_id ({self.start_id}) 不能大于 end_id ({self.end_id})")
                self.id_ls = list(range(self.start_id, self.end_id + 1))

        def _validate_mode_specific_params(self) -> None:
            """验证模式特定参数"""
            if self.mode == _mode.mode2:
                if not self.p1_url:
                    raise ValueError("Config Error: mode2模式下, page_url不能为空")
                if '{}' not in self.p1_url:
                    raise ValueError(f"Config Error: page_url 必须包含 '{{}}' 占位符: {self.p1_url}")
                if not self.p1_url.startswith('http'):
                    raise ValueError(f"Config Error: page_url 格式错误: {self.p1_url}")

    @dataclass
    class p1_return:
        items: List = field(default_factory=list)
        next_url: Optional[str] = None

    @dataclass
    class p2_return:
        id: str
        url: str
        title: str
        author: str
        description: str
        p3s: List[Tuple[str, str]]
        total_p3: int

    @dataclass
    class p3_return:
        p2_title: str
        id: int
        title: str
        url: str
        content: str

    def __init__(self, config: Config, log: Logger = None, MainWindows_ui=None, stop_flag: bool = False,
                 pause_flag: bool = False):
        """初始化爬虫实例

        Args:
            config: 爬虫配置对象
            log: 日志记录器
            MainWindows_ui: 主窗口UI对象
            stop_flag: 停止标志
            pause_flag: 暂停标志
        """
        self.config = config
        self.ui = MainWindows_ui
        self.work_queue: asyncio.Queue = asyncio.Queue()
        self.queue_1: asyncio.Queue = asyncio.Queue()
        self.stop_flag = stop_flag
        self.pause_flag = pause_flag
        self.pause_event = asyncio.Event()
        self.pause_event.set()
        self.session: Optional[Any] = None
        self._session_lock = asyncio.Lock()

        self.log = log or Logger()
        super().__init__(self.log)
        self.__base_pc_init_init()

    async def meet_fanpa(self,e,f,*args,**kwargs):
        self.debug('meet_fanpa')
        self.error(f'====>遇到反爬:{e}')
        time.sleep(20)
        try:
            s = await f(self, *args, **kwargs)
            self.info('继续')
            return s
        except Exception as e:
            self.pause()
            await self.pause_event.wait()
            return await f(self,*args,**kwargs)

    def __base_pc_init_init(self):
        self.req = Requests(Requests.Config(
            proxy_list=self.config.proxy_list,
            max_retries=self.config.max_retries,
            timeout=self.config.timeout,
            cookies=self.config.cookies,
            headers=self.config.headers,
        ), logger=self.log)
        self.threadpool = ThreadPool(max_workers=self.config.threadpool_thread_num, logger=self.log)
        self.asy = Async(logger=self.log)
        self.Directory = Directory(self.config.save_path, logger=self.log)
        self.File_handle = FileHandle(max_open_files=200, logger=self.log)

    def _should_exit(self) -> bool:
        """判断是否应该退出工作循环

        Returns:
            bool: 是否应该退出
        """
        return self.ui is None and self.work_queue.empty() and self.queue_1.empty()

    @staticmethod
    def name(fun):
        return fun.__name__

    def stop(self) -> None:
        """停止爬虫运行"""
        self.stop_flag = True
        self.pause_event.set()

    def pause(self) -> None:
        """暂停爬虫运行"""
        self.pause_flag = True
        self.pause_event.clear()
        self.info("任务已暂停")

    def resume(self) -> None:
        """恢复爬虫运行"""
        self.pause_flag = False
        self.pause_event.set()
        self.info("任务已恢复")

    def _stop(self) -> None:
        """清理资源"""
        self._close_session()
        self._shutdown_threadpool()
        self._cleanup_file_handle()
        self._stop_async()

    def _close_session(self) -> None:
        """关闭HTTP会话"""

        async def close_session():
            try:
                if self.session:
                    await self.session.close()
            except Exception as e:
                self.warning(f"关闭会话时发生异常: {e}")

        if self.asy and self.asy.loop and self.asy.loop.is_running():
            future = asyncio.run_coroutine_threadsafe(close_session(), self.asy.loop)
            try:
                future.result(timeout=self.config.session_close_timeout)
            except asyncio.TimeoutError:
                self.warning("关闭会话超时")
            except Exception as e:
                self.warning(f"关闭会话失败: {e}")

    def _shutdown_threadpool(self) -> None:
        """关闭线程池"""
        if self.threadpool:
            self.threadpool.shutdown()

    def _stop_async(self) -> None:
        """停止异步执行器"""
        if self.asy:
            self.asy.stop()

    def _cleanup_file_handle(self) -> None:
        """清理文件句柄"""
        if self.File_handle:
            self.asy.submit(self.File_handle.close_all())
            # self.File_handle.close_all()

    def __del__(self) -> None:
        """析构函数，确保资源被释放"""
        self._stop()

class _Base_Pc(_Base_Pc_init):
    """异步爬虫基类，支持多种工作模式和运行时控制"""

    
    def __init__(self, config: _Base_Pc_init.Config, log: Logger = None, MainWindows_ui=None, stop_flag: bool = False,
                 pause_flag: bool = False):
        """初始化爬虫实例

        Args:
            config: 爬虫配置对象
            log: 日志记录器
            MainWindows_ui: 主窗口UI对象
            stop_flag: 停止标志
            pause_flag: 暂停标志
        """
        super().__init__(config=config, log=log, MainWindows_ui=MainWindows_ui, stop_flag=stop_flag,
                         pause_flag=pause_flag)
        self.mode_handlers = {
            _mode.mode1:self._mode1,
            _mode.mode2:self._mode2,
            _mode.mode3:self._mode3,
        }

    async def init_session(self, headers: Optional[Dict] = None) -> None:
        """单例模式初始化Session

        Args:
            headers: 请求头信息
        """

        if self.session is None:
            async with self._session_lock:
                if self.session is None:
                    if headers is None:
                        headers = self.config.headers
                    self.session = await self._create_session_impl(headers)
                    await self.init_login()
                    self.info(f'{self.name(self.init_session)}: 创建会话成功')

    async def _create_session_impl(self, headers: Optional[Dict] = None) -> Any:
        """内部实现：创建会话，方便子类仅重写创建逻辑保留单例控制

        Args:
            headers: 请求头信息

        Returns:
            创建的session对象
        """
        return await self.req.async_create_session(headers=headers)

    async def init_login(self) -> None:
        """子类覆盖此方法实现登录逻辑"""
        pass

    def change_session_cookies(self, cookies, session=None):
        if session is None:
            session = self.session
        self.req.update_cookies(session, cookies)

    def add_task(self, work_id: Any) -> None:
        """动态添加任务接口 (供UI使用)

        Args:
            work_id: 工作任务ID
        """
        try:
            if self.asy and self.asy.loop and self.asy.loop.is_running():
                self.asy.loop.call_soon_threadsafe(self.work_queue.put_nowait, work_id)
            else:
                self.work_queue.put_nowait(work_id)
            self.info(f"动态添加任务: {work_id}")
        except Exception as e:
            self.error(f"添加任务失败: {e}")

    async def parse_html(self, func, *args, **kwargs) -> Any:
        """在线程池中运行CPU密集型解析任务

        Args:
            func: 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            函数执行结果
        """
        return await asyncio.wrap_future(self.threadpool.submit(func, *args, **kwargs))

    async def work(self, work_id: Any) -> None:
        """具体业务逻辑，子类需实现

        Args:
            work_id: 工作任务ID
        """
        raise NotImplementedError("Subclasses must implement work method")

    async def _base_mode(self, work_id: Any) -> None:
        """基础模式处理逻辑

        Args:
            work_id: 工作任务ID
        """
        try:
            await self.init_session()
            await self.work(work_id)
        except asyncio.CancelledError:
            self.info(f"Work ID {work_id} cancelled")
            raise
        except Exception as e:
            self.error(f"Work ID {work_id} failed: {e}")

    async def _worker(self) -> None:
        """工作协程，从队列中获取任务并处理"""
        await asyncio.sleep(self.config.worker_startup_delay)
        while True:
            if self.stop_flag:
                break

            await self.pause_event.wait()

            if self._should_exit():
                break

            try:
                work_id = await asyncio.wait_for(self.work_queue.get(), timeout=self.config.queue_get_timeout)
                await self._base_mode(work_id)
                self.work_queue.task_done()
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                self.info("Worker cancelled")
                if not self.work_queue.empty():
                    self.work_queue.task_done()
                raise
            except Exception as e:
                self.error(f"Worker error: {e}")

    async def _mode1(self) -> None:
        """模式1: 生产者-消费者模型

        将init_queue中的任务转移到work_queue，然后启动多个worker并发处理
        """
        await self._transfer_init_to_work_queue()
        tasks = [self._worker() for _ in range(self.config.max_workers)]
        await self.asy.submit_inside_s(tasks, return_exceptions=True)

    async def _mode2(self) -> None:
        """模式2: 页面爬取模式 (生产者-消费者并发)

        生产者从init_queue获取页面ID，处理页面后将items放入work_queue
        消费者从work_queue获取items进行处理
        """

        async def _producer() -> None:
            """生产者协程，处理页面并生成工作项"""
            while not self.queue_1.empty():
                if self.stop_flag:
                    break
                page_id = '未获取的id'
                try:
                    page_id = self.queue_1.get_nowait()
                    self.info(f"处理页面级id: {page_id}...")

                    items = await self._process_page(page_id)

                    if items:
                        for item in items:
                            await self.work_queue.put(item)
                        self.info(f"Page {page_id} done. Added {len(items)} items.")
                    else:
                        self.warning(f"页面没有元素： {page_id}")

                    self.queue_1.task_done()

                except asyncio.QueueEmpty:
                    pass

                except asyncio.CancelledError:
                    self.info("任务取消")
                    if not self.queue_1.empty():
                        self.queue_1.task_done()
                    raise

                except Exception as e:
                    self.error(f"{_mode.mode2} 出错： {page_id}: {e}")
                    self.queue_1.task_done()

        tasks = [_producer()] + [self._worker() for _ in range(self.config.max_workers)]
        await self.asy.submit_inside_s(tasks, return_exceptions=True)

    async def _mode3(self) -> None:
        pass

    async def _transfer_init_to_work_queue(self) -> None:
        """将init_queue中的任务转移到work_queue"""
        while not self.queue_1.empty():
            if self.stop_flag:
                break
            try:
                work_id = self.queue_1.get_nowait()
                await self.work_queue.put(work_id)
            except asyncio.QueueEmpty:
                break

    async def _process_page(self, page_id: int) -> list:
        """模式2专用：处理单个页面，返回该页面包含的所有工作项列表

        Args:
            page_id: 页面ID

        Returns:
            该页面包含的所有工作项列表

        Raises:
            NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError("Mode2 requires implementing process_page(page_id)")

    async def _run(self) -> None:
        """运行爬虫的主逻辑"""
        self._initialize_task_queue()
        await self.init_session()
        await self._execute_mode()

    def _initialize_task_queue(self) -> None:
        """初始化任务队列"""
        for work_id in self.config.id_ls:
            self.queue_1.put_nowait(work_id)

    async def _execute_mode(self) -> None:
        """执行配置的工作模式"""

        handler = self.mode_handlers.get(self.config.mode)
        if handler:
            await handler()
        else:
            self.error(f"未知模式: {self.config.mode}")

    def run(self, blocking: bool = True) -> Optional[Any]:
        """入口方法，启动爬虫

        Args:
            blocking: 是否阻塞等待完成

        Returns:
            如果blocking为False，返回Future对象；否则返回None
        """
        try:
            res = self.asy.submit(self._run(), await_result=blocking)
            if blocking:
                self.info('全部任务流程结束')
            return res
        except KeyboardInterrupt:
            self.warning("用户强制停止")
        finally:
            if blocking:
                self._stop()

class BaseManager(Ljp_BaseClass):
    p1_return = _Base_Pc.p1_return
    p2_return = _Base_Pc.p2_return
    p3_return = _Base_Pc.p3_return

    def __init__(self,pc,data:p2_return,file_handle,log:Logger):
        self.pc = pc
        self.data = data
        self.file_handle = file_handle
        self.logger = log
        self.expected_id = 1
        self.pending = {}
        self._lock = asyncio.Lock()

        self._initialized = False
        super().__init__(self.logger)

    async def add_p3(self,p3:_Base_Pc.p3_return):
        raise
    
    async def init(self):
        if self._initialized:
            return True
        self._initialized = True
        try:
            await self.target_init()
        except Exception as e:
            self.error(f"初始化管理器 {self.data.title} 失败: {e}")
            return False
        self.info(f"初始化管理器: {self.data.title}")
        return True
    
    async def target_init(self) -> None:
        pass

    def finish(self):
        self.info(f"管理器完成: {self.data.title}")

    @staticmethod
    def sanitize_filename(title: str) -> str:
        return re.sub(r'[\\/:*?"<>|]', '_', title)

    @staticmethod
    def get_file_path(title: str) -> str:
        return title + '.txt'
    
    def _get_p_mode(self,title: str,index:int) -> str:
        return title

class Pc(_Base_Pc):
    def __init__(self, config: _Base_Pc.Config, log: Logger = None, MainWindows_ui=None, stop_flag: bool = False,
                 pause_flag: bool = False):
        super().__init__(config=config, log=log, MainWindows_ui=MainWindows_ui, stop_flag=stop_flag,
                         pause_flag=pause_flag)
        
        self.manager = self.get_manager()

    @Ljp_Decorator.handle_exceptions(MeetCheckError,_Base_Pc.meet_fanpa)
    async def get(self,session,url,*args,**kwargs) -> Any:
        self.debug(f'session_type:{session},url:{url}',self.get)
        return await self.req.async_get(session=session,url=url,*args,**kwargs)

    async def _process_page(self, page_id: int) -> list:
        """
        处理单页抓取
        """
        url = self.config.p1_url.format(page_id)
        all_items = []

        try:
            html_str = await self.get(session=self.session,url=url)
            self.debug(f'html_str:{html_str}',self._process_page)
            if html_str:
                result = await self.parse_html(self._parse_p1, html_str,url)
                if result:
                    items, next_url = result.items,result.next_url
                    self.debug(items)
                    if items:
                        all_items.extend(items)
        except MeetCheckError as e:
            self.debug(f'遇到反爬:{e}')
            raise
        except Exception as e:
            self.error(f"Process page {page_id} error: {e}")

        return all_items

    def _parse_p1(self,res_html,url)->tuple[list,str|None]|_Base_Pc.p1_return:
        return self.p1_return(*self.parse_p1(res_html,url))

    def _parse_p2(self,res_html,url:str):
        return self.parse_p2(res_html,url)

    def _parse_p3(self,res_html,url):
        return self.parse_p3(res_html,url)

    def parse_p1(self,res_html,url):
        '''
        解析p1页面，返回列表和下一页URL
        Args:
            res_html: 页面HTML内容
            url: 页面URL
        Returns:
            列表和下一页URL元组(items,next_url)
        '''
        raise NotImplementedError("parse_p1 方法未实现")
    
    def parse_p2(self,res_html,url)->tuple[str,str,str,list[tuple[str,str]],str|None]:
        '''
        解析p2页面，返回详情
        Args:
            res_html: 页面HTML内容
            url: 页面URL
        Returns:
            详情元组(title,author,description,p3s(列表加元组)),next_url
        '''
        raise NotImplementedError("parse_p2 方法未实现")
    
    def parse_p3(self,res_html,url)->tuple[str,str,str|None]:
        '''
        解析p3页面，返回详情
        Args:
            res_html: 页面HTML内容
            url: 页面URL
        Returns:
            详情元组(title,content,next_url)
        '''
        raise NotImplementedError("parse_p3 方法未实现")


    #====================================================================#
    async def _fetch_p2(self, p2_id: str):
        f = self._fetch_p2
        """异步获取p2页面内容"""
        p2_url = self.config.p2_url.format(p2_id)
        current_url = p2_url
        full_content = []
        title, author, description='','',''
        while current_url:
            if self.stop_flag:
                break
            await self.pause_event.wait()
            try:
                html_str = await self.get(session=self.session, url=current_url)
                if not html_str:
                    self.warning(f"空响应 for p2 {p2_id}")
                    raise No(f"空响应:{p2_id}")
                res = await self.parse_html(self._parse_p2, html_str, current_url)
                if not res:
                    raise No('res为空')
                tit, aut, des, p3s,next_url = res
                if not title:
                    title = tit
                if not author:
                    author = aut
                if not description:
                    description = des
                if p3s:
                    full_content.extend(p3s)
                else:
                    self.warning(f'_fetch_p2{current_url}获取p2列表为空',)

                if (not next_url) or (next_url==p2_url):
                    break
                current_url = next_url

            except MeetCheckError:
                continue

            except Exception as e:
                self.error(f"{current_url}获取失败,id:{p2_id},e:{e}")
                raise No(f'{current_url}获取失败,id:{p2_id}',f=f,e=e)

        return self.p2_return(
            id=p2_id,
            url=p2_url,
            title=title,
            author=author,
            description=description,
            p3s=full_content,
            total_p3=len(full_content),
        )

    async def download(self,p2_results):
        '''
        下载p2页面内容
        Args:
            p2_results: p2页面详情
        '''
        try:
            safe_title = self.manager.sanitize_filename(p2_results.title)
            path = self.manager.get_file_path(title=safe_title)
            file_path = self.Directory.get_file_path(path)
            # 获取文件句柄(影视需要额外实现)
            file_handle = await self._get_file_handle(file_path)

            manager = self.manager(self,p2_results, file_handle, self.log)
            if not await manager.init():
                return

            tasks = []
            for i,p3 in enumerate(p2_results.p3s):
                p3_id = i + 1
                res = self._parse_p3_info(p3_id,p3,p2_results.title,manager)
                if res:
                    tasks.append(res)
            await self.asy.submit_inside_s(tasks)
            await manager.finish()
        except Exception as e:
            self.error(f'出错:{e}',self.download.__name__)
            raise No(f'{self.download.__name__}出错',e)

    async def _parse_p3_info(self,p3_id:int,p3:Tuple[str,str],p2_title:str,manager:BaseManager)->tuple[int,int,str,str,str]|None:
        '''
        解析p3页面内容
        Args:
            p3_id: p3页面ID
            p3: p3页面地址元组(title,url)
            p2_title: p2页面标题
            manager: 管理器
        Returns:
            详情元组(p2_id,p3_id,title,url,content)
        '''
        current_url = p3[1]
        full_content = []
        p3_title = p3[0]
        while current_url:
            if self.stop_flag:
                break
            await self.pause_event.wait()
            try:
                html_str = await self.get(session=self.session, url=current_url)
                if not html_str:
                    self.warning(f"空响应 for p3 {p3_id}")
                    break
                result = await self.parse_html(self._parse_p3, html_str, current_url)
                if not result:
                    self.error(f"解析p3 {p3_id} 失败: {current_url}")
                    break
                ptitle, content, next_page_url = result
                if not p3_title:
                    p3_title = ptitle
                if content:
                    full_content.append(content)
                else:
                    full_content.append(None)
                if next_page_url:
                    current_url = next_page_url
                    if current_url == p3[1]:
                        break
                else:
                    break
            except MeetCheckError:
                continue
  
            except Exception as e:
                self.error(f"Fetch p3 {p3_id},url:{current_url} error: {e}")
                break
        p3 = self.p3_return(
            p2_title=p2_title,
            id=p3_id,
            title=p3_title,
            url=p3[1],
            content="\n".join([i for i in full_content if i is not None and str(i).strip() != '']),
        )
        await manager.add_p3(p3)

    async def work(self,work_id):
        '''
        单个任务执行具体逻辑
        '''
        try:
            p2_results = await self._fetch_p2(work_id)
            if self.ui:
                await self.ui.add_p2(p2_results)
            else:
                await self.download(p2_results)
        except Notfound as e:
            self.warning(f"不存在 ID: {work_id},error:{e}")
        except Exception as e:
            self.error(f"Work {work_id} error: {e}")

    def get_manager(self):
        self.manager = None
        raise NotImplementedError("get_manager 方法未实现")

    async def _get_file_handle(self,file_path:str):
        '''
        Ys 需要额外实现
        :param file_path:
        :return:
        '''
        return await self.File_handle.get(file_path)

class Ys(Pc):
    class Manager(BaseManager):
        def __init__(self,pc,data:_Base_Pc.p2_return,file_handle,log):
                super().__init__(pc,data = data,file_handle=file_handle,log=log)

    def __init__(self, config: Pc.Config, log: Logger = None, MainWindows_ui=None, stop_flag: bool = False,
                 pause_flag: bool = False):
        super().__init__(config=config, log=log, MainWindows_ui=MainWindows_ui, stop_flag=stop_flag,
                         pause_flag=pause_flag)
    
    def get_manager(self):
        self.manager = self.Manager
        return self.manager

if __name__ == '__main__':
    pass
















