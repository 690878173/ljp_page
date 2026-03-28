
import sys
import subprocess
import os
def get_pip_ls(l,upgrade=False):
    ls = [sys.executable, '-m', 'pip', 'install']
    if upgrade:
        ls.append('--upgrade')
    else:
        ls.extend(["--no-deps", "--ignore-requires-python"])
    ls.extend(l)
    return ls

def cmd_d(cmd):
    result = subprocess.run(cmd, check=True, env=os.environ.copy(), timeout=300, capture_output=True, text=True)
    return result

def download(pg):
    try:
        cmd = get_pip_ls(l=[pg])
        result = cmd_d(cmd)
        print("安装成功：", result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"安装失败:{pg}")
        print(f"错误详情：{e.stderr}")

def check_build():
    try:
        print('正在检查构建工具版本')
        cmd = get_pip_ls(l=['pip', 'setuptools', 'wheel'],upgrade=True)
        res = cmd_d(cmd)
        print("构建工具升级成功：", res.stdout)
    except Exception as e:
        print("升级构建工具失败：", str(e))

if __name__ == '__main__':
    download('https://github.com/690878173/ljp_page/archive/refs/heads/master.zip')