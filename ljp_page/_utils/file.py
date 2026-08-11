import json
from pathlib import Path


class File:

    @staticmethod
    def path(file_path):
        return Path(file_path)

    @staticmethod
    def create_dir(file_path):
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def load_json(file_path,encoding="utf-8"):
        File.create_dir(file_path)
        fp = File.path(file_path)
        try:
            with open(fp, "r", encoding=encoding) as f:
                return json.load(f)
        except Exception as e:
            print(f"加载失败: {fp}, {e}")
            return {}

    @staticmethod
    def save_json(file_path, data,encoding="utf-8"):
        File.create_dir(file_path)
        fp = File.path(file_path)
        try:
            with open(fp, "w", encoding=encoding) as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"json保存失败: {fp}, {e}")

__all__ = ['File']

