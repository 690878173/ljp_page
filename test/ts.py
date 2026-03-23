import sys

import requests
import zipfile
import os

url = 'https://codeload.github.com/690878173/ljp_page/zip/refs/heads/master'
# r = requests.get(url)
# with open("pkg.zip", "wb") as f:
#     f.write(r.content)
#
# with zipfile.ZipFile("pkg.zip", "r") as zip_ref:
#     zip_ref.extractall(".")
#
# # 3. 安装
# os.system(f"{sys.executable} -m pip install ./ljp_package-main")

print("安装完成")


def _install():
    import sys
    import subprocess
    print(sys.executable)
    urls = [
        "git+https://gitee.com/pangjinglin/ljp_package.git",
        "git+https://github.com/690878173/ljp_page.git"
    ]
    for url in urls:
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install",
                "--no-deps",
                "--upgrade",
                url
            ], check=True)
            print(f"安装成功: {url}")
            return
        except:
            print(f"失败，尝试下一个源: {url}")

    print("全部源都失败")