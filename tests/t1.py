import os
import shutil
import subprocess
from pathlib import Path

# 👉 改成你的7z路径（一般就是这个）
SEVEN_ZIP = r"D:\d\app_up\7z\7-Zip\7z.exe"


def is_archive(file_path: Path):
    return file_path.suffix.lower() in [".zip", ".rar", ".7z", ".tar", ".gz"]


def extract_archive(file_path: Path):
    try:
        subprocess.run(
            [SEVEN_ZIP, "x", str(file_path), f"-o{file_path.parent}", "-y"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        print(f"[解压] {file_path}")
        return True
    except Exception as e:
        print(f"[失败] {file_path} -> {e}")
        return False


def extract_all(root_dir: Path):
    processed = set()
    changed = True

    while changed:
        changed = False

        for root, _, files in os.walk(root_dir):
            for f in files:
                file_path = Path(root) / f

                if file_path in processed:
                    continue

                if is_archive(file_path):
                    ok = extract_archive(file_path)
                    processed.add(file_path)
                    if ok:
                        changed = True


def get_unique_path(root_dir: Path, name: str):
    target = root_dir / name
    if not target.exists():
        return target

    stem = Path(name).stem
    suffix = Path(name).suffix
    i = 1

    while True:
        new = root_dir / f"{stem}_{i}{suffix}"
        if not new.exists():
            return new
        i += 1


def collect_pptx(root_dir: Path):
    count = 0

    for root, _, files in os.walk(root_dir):
        for f in files:
            file_path = Path(root) / f

            if file_path.suffix.lower() in [".pptx",'.ppt']:
                if file_path.parent == root_dir:
                    continue

                target = get_unique_path(root_dir, f)

                try:
                    shutil.move(str(file_path), str(target))
                    print(f"[移动] {file_path} -> {target}")
                    count += 1
                except Exception as e:
                    print(f"[失败] {file_path} -> {e}")

    print(f"\n共收集 {count} 个 PPTX 文件")


def main():
    folder = r'E:\BaiduNetdiskDownload\PPT模版分类'
    root = Path(folder)

    if not root.exists():
        print("目录不存在")
        return

    print("\n=== 开始解压 ===")
    extract_all(root)

    print("\n=== 收集 PPTX ===")
    collect_pptx(root)

    print("\n完成 ✅")


if __name__ == "__main__":
    main()