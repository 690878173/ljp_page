import os
import asyncio
from ..._ljp_coro.base_class import Ljp_BaseClass

class Ffmpeg(Ljp_BaseClass):
    def __init__(self,if_delete=True,thread_pool=None,asy=None,logger=None):
        super().__init__()
        self.if_delete = if_delete
        self.thread_pool = thread_pool
        self.asy = asy
        self.logger = logger


    async def merge_with_ffmpeg(self, directory, file_name):
        """
        使用ffmpeg合并ts文件
        :param file_name: 合并后的文件名
        :param directory: ts文件所在目录
        """
        f_name = Ffmpeg.merge_with_ffmpeg.__name__
        try:
            # 获取所有ts文件并按数字顺序排序
            ts_files = sorted(
                [f for f in os.listdir(directory) if f.endswith('.ts')],
                key=lambda x: int(x.split('.')[0])
            )

            if not ts_files:
                self.warning(f"目录 {directory} 中没有找到ts文件")
                return

            # 创建文件列表
            list_file = os.path.join(directory, 'filelist.txt')
            with open(list_file, 'w', encoding='utf-8') as f:
                for ts_file in ts_files:
                    f.write(f"file '{ts_file}'\n")

            # 构建输出文件路径
            output_file = os.path.join(directory, f'{file_name}.mp4')

            # 执行ffmpeg命令
            command = [
                'ffmpeg',
                '-loglevel', 'error',
                '-f', 'concat',
                '-safe', '0',
                '-i', list_file,
                '-c', 'copy',
                '-y',  # 覆盖已存在的文件
                output_file
            ]
            # 异步创建子进程（替代 subprocess.run）
            proc = await asyncio.create_subprocess_exec(
                *command,
                cwd=directory,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            # 等待子进程完成，并获取输出（stdout/stderr）

            # 模拟同步版本的 check=True：若返回码非 0，抛出异常
            if proc.returncode != 0:
                self.error(f"合并失败：{stderr.decode()}",f_name=f_name)
                return
            else:
                self.info(f"合并成功：{output_file}")
            os.remove(list_file)
            if self.if_delete:
                for ts_file in ts_files:
                    os.remove(os.path.join(directory, ts_file))

            self.info(f"文件合并完成,输出目录为: {output_file}",f_name=f_name)
            return output_file

        except Exception as e:
            self.error(f"合并ts文件失败 目录: {directory}, 错误: {e}",f_name=f_name)

    async def create_task(self, directory, file_name):
        """
        创建合并任务
        :param directory: ts文件所在目录
        :param file_name: 合并后的文件名
        """
        if self.asy:
            await self.asy.submit_inside(self.merge_with_ffmpeg(directory, file_name))
        else:
            raise NotImplementedError("异步任务池未配置")

    def test_create_task(self,directory, file_name):
        tas = self.asy.submit(self.create_task(directory, file_name),if_result=True)

# 调用
if __name__ == "__main__":
    pass