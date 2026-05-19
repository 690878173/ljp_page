from pathlib import Path

import os


def to_path(str_):
    return Path(str_)

def create_dir(path):
    try:
        os.makedirs(path, exist_ok=True)
    except Exception as e:
        raise f'创建文件夹出错{e}'

