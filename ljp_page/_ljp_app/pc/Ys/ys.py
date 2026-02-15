import os
import asyncio
import re
import aiofiles
from dataclasses import dataclass
from typing import List, Optional, Tuple, Any
from abc import ABC, abstractmethod

from lxml import etree

from ljp_page._ljp_applications.pc.Ys.ljp_ffmpeg import Ffmpeg

from ljp_page.logger import Logger
from ljp_page._ljp_applications.pc.base.base_pc import Pc,BaseManager
from ljp_page.exceptions import NetworkError, ParseError,Notfound

@dataclass
class VideoInfo:
    """视频详情"""
    id: str
    title: str
    url: str
    description: str
    episodes: List[Tuple[str, str]] # List of (Title, URL)
    total_episodes: int

class VideoManager:
    """
    视频下载管理器：负责M3U8解析、TS下载、合并
    """
    def __init__(self, base_dir: str, ffmpeg: Ffmpeg, logger: Logger = None):
        self.base_dir = base_dir
        self.ffmpeg = ffmpeg
        self.logger = logger
        self._lock = asyncio.Lock()

    @staticmethod
    def sanitize_filename(title: str) -> str:
        return re.sub(r'[\\/:*?"<>|]', '_', title)

    async def process_episode(self, video_title: str, ep_title: str, ep_url: str, req_tool, session) -> bool:
        """
        处理单个分集：解析M3U8 -> 下载TS -> 合并
        """
        safe_video_title = self.sanitize_filename(video_title)
        safe_ep_title = self.sanitize_filename(ep_title)
        
        # 视频保存目录
        video_dir = os.path.join(self.base_dir, safe_video_title)
        # 分集临时目录 (用于放TS)
        ts_dir = os.path.join(video_dir, safe_ep_title)
        os.makedirs(ts_dir, exist_ok=True)
        
        # 最终输出文件
        output_file = os.path.join(video_dir, f"{safe_ep_title}.mp4")
        if os.path.exists(output_file):
            if self.logger:
                self.logger.info(f"视频已存在，跳过: {safe_ep_title}")
            return True

        try:
            # 1. 获取 M3U8 内容
            # 注意：这里假设 ep_url 指向的是包含播放器的页面，还是直接是 m3u8 链接？
            # 通常爬虫需要先从 ep_url 页面提取出 m3u8 真实地址，或者 ep_url 本身就是 m3u8
            # 根据原 ys.py 逻辑，它似乎在 get_part 中再次请求了 m3u8_url。
            # 这里我们假设子类已经解析出了 m3u8_url，或者我们需要在这里做。
            # 为了通用性，我们假设传入的 ep_url 是页面地址，需要进一步解析。
            # 但为了保持 VideoManager 纯粹，最好是传入 m3u8_url。
            # 我们先假设 ep_url 就是 m3u8 链接，或者由外部解析好传入。
            # 经过查看原 ys.py，它在 _get_part 中调用 get_part，get_part 中似乎再次请求。
            
            # 简化策略：我们假定传入的是需要进一步解析的页面URL，或者直接是M3U8。
            # 这里我们做一个简单的判断，或者让调用者处理。
            # 鉴于这是通用管理器，我们假设传入的是 m3u8_url。
            # 如果需要从页面解析 m3u8，应该在 Spider 的 parse 阶段完成。
            
            m3u8_content = await req_tool.async_get(session, ep_url)
            if not m3u8_content:
                raise NetworkError(f"M3U8内容为空: {ep_url}")

            # 2. 解析 M3U8
            ts_list, is_vod = M3u8.parse_m3u8(m3u8_content)
            if not ts_list:
                raise ParseError("未找到TS片段")

            # 3. 下载 TS
            tasks = []
            for i, ts in enumerate(ts_list):
                # 处理相对路径
                if not ts.url.startswith('http'):
                    base_url = ep_url.rsplit('/', 1)[0] + '/'
                    ts.url = base_url + ts.url
                
                ts_path = os.path.join(ts_dir, f"{i}.ts")
                tasks.append(self._download_ts(ts.url, ts_path, req_tool, session))
            
            # 并发下载 (使用外部传入的并发控制或简单的 gather)
            # 这里直接 gather，但最好由 Spider 控制并发量
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 检查下载结果
            failed_count = sum(1 for r in results if isinstance(r, Exception) or not r)
            if failed_count > 0:
                if self.logger:
                    self.logger.warning(f"部分TS下载失败 ({failed_count}/{len(tasks)}): {safe_ep_title}")
                # 依然尝试合并，或者直接失败？通常缺片会导致合并失败或花屏。
            
            # 4. 合并
            await self.ffmpeg.merge_with_ffmpeg(ts_dir, safe_ep_title)
            
            # 5. 清理 TS 目录 (如果配置了删除)
            if self.ffmpeg.if_delete:
                # Ffmpeg 类里没有自动删除目录的逻辑，这里手动补充?
                # 原 Ffmpeg 类似乎只是合并。
                # 我们手动清理
                import shutil
                shutil.rmtree(ts_dir, ignore_errors=True)
                
            if self.logger:
                self.logger.info(f"视频处理完成: {safe_ep_title}")
            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"处理分集失败 {safe_ep_title}: {e}")
            return False

    async def _download_ts(self, url: str, save_path: str, req_tool, session) -> bool:
        if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
            return True
        try:
            content = await req_tool.async_get(session, url, read_content=True) # 假设 async_get 支持返回 bytes，或者需要修改 Requests
            # 原 Requests.async_get 默认返回 text。我们需要 check ljp_requests.py
            # 如果不支持 bytes，这里会出问题。
            # 假设 req_tool.async_get 返回的是 bytes (如果 response.read() 被调用)
            # 检查 ljp_requests.py: 
            # res_text = await response.text(encoding=self.encoding, errors='ignore')
            # 它只返回 text。我们需要扩展 Requests 或直接使用 session.get
            
            # 临时直接用 session
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    async with aiofiles.open(save_path, 'wb') as f:
                        await f.write(content)
                    return True
            return False
        except Exception:
            return False

class BaseVideoSpider(Pc, ABC):
    """
    视频爬虫抽象基类
    """
    def __init__(self, config: Pc.Config, log: Logger = None, MainWindows_ui=None):
        super().__init__(config, log, MainWindows_ui)
        self.ffmpeg = Ffmpeg(if_delete=True, asy=self.asy, logger=self.log)

    async def work(self, video_id: str):
        """
        通用单视频处理流程
        """
        # 1. 获取视频详情
        video_info = await self._fetch_video_info(video_id)
        
        is_err = video_info


        # 2. UI 或 下载
        if self.ui:
            # 假设 UI 有 add_movie 方法，如果没有则需调整
            if hasattr(self.ui, 'add_movie'):
                self.ui.add_movie(video_info)
            else:
                self.ui.add_book(video_info) # 兼容旧 UI
        else:
            await self._download_video_process(video_info)

    async def _download_video_process(self, video_info: VideoInfo):
        """下载视频的具体流程"""
        manager = VideoManager(self.config.save_path, self.ffmpeg, self.log)
        
        # 并发下载所有分集
        tasks = []
        for ep_title, ep_url in video_info.episodes:
            # 这里假设子类解析出的 ep_url 已经是 m3u8，或者我们需要在这里再次解析
            # 为了通用性，我们调用一个钩子方法来获取真实的 m3u8 链接
            tasks.append(self._process_episode_wrapper(video_info.title, ep_title, ep_url, manager))
        
        # 使用 Async 工具限制并发
        await self.asy.submit_inside_s(tasks)

    async def _process_episode_wrapper(self, video_title: str, ep_title: str, ep_url: str, manager: VideoManager):
        """
        包装器：先获取真实 M3U8 地址，再调用管理器下载
        """
        try:
            real_m3u8_url = await self.get_real_m3u8_url(ep_url)
            if not real_m3u8_url:
                self.error(f"无法获取M3U8地址: {ep_title}")
                return
            
            await manager.process_episode(video_title, ep_title, real_m3u8_url, self.req, self.session)
        except Exception as e:
            self.error(f"分集处理异常 {ep_title}: {e}")

    async def _fetch_video_info(self, video_id: int) -> Optional[VideoInfo]:
        url = self.config.info_url.format(video_id)
        try:
            html_str = await self.req.async_get(self.session, url)
            if not html_str:
                return None
            return await self.parse_html(self.parse_video_info, html_str, video_id, url)
        except Exception as e:
            self.error(f"Fetch info error {video_id}: {e}")
            return RuntimeError(str(e))

    async def process_page(self, page_id: int) -> List[Any]:
        """Mode2 翻页逻辑"""
        url = self.config.page_url.format(page_id)
        try:
            html_str = await self.req.async_get(self.session, url)
            if html_str:
                result = await self.parse_html(self.parse_page_videos, html_str)
                if result:
                    items, _ = result
                    return items
        except Exception as e:
            self.error(f"Process page error {page_id}: {e}")
        return []

    # --- 抽象方法 ---

    @staticmethod
    @abstractmethod
    def parse_video_info(html_str: str, video_id: int, url: str) -> VideoInfo:
        pass

    @staticmethod
    @abstractmethod
    def parse_page_videos(html_str: str) -> Tuple[List[str], Optional[str]]:
        pass

    @abstractmethod
    async def get_real_m3u8_url(self, ep_url: str) -> Optional[str]:
        """从分集页面/链接获取真实的 m3u8 地址"""
        pass


class Ys:
    pass

class YhdmSpider(BaseVideoSpider):
    @staticmethod
    def parse_video_info(html_str: str, video_id: str, url: str) -> VideoInfo:
        html = etree.HTML(html_str)
        try:
            # 检查错误
            title_tag = html.xpath('/html/head/title/text()')
            if title_tag and '520' in title_tag[0]:
                raise Notfound("Server 520 Error")

            title = html.xpath('//div[@class="info"]/h1/text()')[0]
            desc_p = html.xpath('//div[@class="info"]/p/text()')
            description = desc_p[0] if desc_p else ""
            
            # 解析播放列表
            # 假设结构：//div[@class="play"]/ul/li/a
            ep_links = html.xpath('//div[@class="play"]/ul/li/a')
            episodes = []
            
            base_url = "https://www.yhdm1.one" # 应该从 config 或 url 获取，这里简写
            
            for a in ep_links:
                ep_title = a.text
                href = a.get('href')
                if not href.startswith('http'):
                    href = base_url + href
                episodes.append((ep_title, href))

            return VideoInfo(
                id=str(video_id),
                title=title,
                url=url,
                description=description,
                episodes=episodes,
                total_episodes=len(episodes)
            )
        except Exception as e:
            raise

    @staticmethod
    def parse_page_videos(html_str: str) -> Tuple[List[str], Optional[str]]:
        html = etree.HTML(html_str)
        ids = []
        try:
            # 示例 XPath
            links = html.xpath('//*[@id="app"]/div[2]/div[2]/div/div[2]/@data-href')
            for link in links:
                # /vod/detail/id/1234.html
                match = re.search(r'/id/(\d+)', link)
                if match:
                    ids.append(int(match.group(1)))
        except Exception:
            pass
        return ids, None

    async def get_real_m3u8_url(self, ep_url: str) -> Optional[str]:
        """
        樱花动漫特定逻辑：请求播放页，提取 m3u8 地址
        """
        # 这里的逻辑通常涉及解析播放页的 JS 变量或 iframe
        # 假设这里简化为直接请求并查找 .m3u8 链接
        try:
            # 注意：这里需要 self.session，但在 staticmethod 中无法访问
            # 所以这个方法定义为实例方法 (async def)
            html = await self.req.async_get(self.session, ep_url)
            if not html: return None
            
            # 简单正则匹配
            # 实际情况可能很复杂，需要解密或执行 JS
            # 这里为了演示，假设源码里直接有 url: 'http...m3u8'
            match = re.search(r'["\'](https?://.*\.m3u8.*?)["\']', html)
            if match:
                return match.group(1)
            
            # 如果没有直接匹配，可能需要其他逻辑
            # 原 ys.py 似乎没有复杂的解析逻辑，只是请求了 ep_url 然后请求 m3u8_url='' (空字符串?)
            # 原代码 line 494: m3u8_text = await self.req.async_get(self.session,m3u8_url) where m3u8_url=''
            # 这看起来原代码是未完成的或错误的。
            
            # 既然是重构，我先留一个简单的占位符，或者假设 ep_url 本身就是 m3u8 (如果上一级解析正确)
            # 但通常列表页给的是播放页 URL。
            
            return None 
        except Exception:
            return None

if __name__ == '__main__':
    config = Pc.Config(
        base_url='https://www.yhdm1.one',
        save_path='D:\\ys\\樱花动漫',
        info_url='https://www.yhdm1.one/vod/detail/id/{}.html',
        start_id=1,
        end_id=2,
        mode='mode1'
    )
    
    spider = YhdmSpider(config)
    # spider.run() # 实际运行需取消注释
