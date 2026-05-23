import base64

import os
import re
from html import unescape
from html.parser import HTMLParser

import aiohttp

from ljp_page._module.request.brower.pydoll.exceptions import InvalidBrowserPath, InvalidResponse, NetworkError


class TextExtractor(HTMLParser):
    """用于文本提取的 HTML 解析器。

    从 HTML 字符串中提取可见文本内容，不包括
    _skip_tags 中指定的标签。"""

    def __init__(self):
        super().__init__()
        self._parts = []
        self._skip = False
        self._skip_tags = {'script', 'style', 'template'}

    def handle_starttag(self, tag, attrs):
        """标记解析器跳过 _skip_tags 中指定的标签内的内容。

        参数：
            tag (str)：标签名称。
            attrs（列表）：（属性，值）对的列表。"""
        if tag in self._skip_tags:
            self._skip = True

    def handle_endtag(self, tag):
        """将解析器标记为跳过标签的末尾。

        参数：
            tag (str)：标签名称。"""
        if tag in self._skip_tags:
            self._skip = False

    def handle_data(self, data):
        """处理文本节点。将它们添加到结果中，除非它们位于跳过标记内。

        参数：
            data (str)：文本数据。"""
        if not self._skip:
            self._parts.append(unescape(data))

    def get_strings(self, strip: bool):
        """产生所有收集的可见文本片段。

        参数：
            strip (bool): 是否从每个片段中去除前导/尾随空白。

        产量：
            str：可见文本片段。"""
        for text in self._parts:
            yield text.strip() if strip else text

    def get_text(self, separator: str, strip: bool) -> str:
        """返回所有可见文本。

        参数：
            分隔符 (str)：在提取的文本片段之间插入的字符串。
            strip (bool): 是否从每个片段中去除空格。

        返回：
            str：可见文本。"""
        return separator.join(self.get_strings(strip=strip))


def extract_text_from_html(html: str, separator: str = '', strip: bool = False) -> str:
    """从 HTML 字符串中提取可见文本内容。

    参数：
        html (str)：从中提取文本的 HTML 字符串。
        分隔符（str，可选）：在提取的文本片段之间插入的字符串。默认为“”。
        strip (bool, 可选): 是否从文本片段中去除空格。默认为 False。

    返回：
        str：提取的可见文本。"""
    parser = TextExtractor()
    parser.feed(html)
    return parser.get_text(separator=separator, strip=strip)


def decode_base64_to_bytes(image: str) -> bytes:
    """将 Base64 图像字符串解码为字节。

    参数：
        image (str)：要解码的 Base64 图像字符串。

    返回：
        bytes：以字节形式解码的图像。"""
    return base64.b64decode(image.encode('utf-8'))


async def get_browser_ws_address(port: int) -> str:
    """获取浏览器实例的 WebSocket 地址。

    返回：
        str：浏览器的 WebSocket 地址。

    加薪：
        NetworkError：如果由于网络错误而无法获取地址
            或丢失数据。
        InvalidResponse：如果响应不是有效的 JSON。"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'http://localhost:{port}/json/version') as response:
                response.raise_for_status()
                data = await response.json()
                return data['webSocketDebuggerUrl']

    except aiohttp.ClientError as e:
        raise NetworkError(f'Failed to get browser ws address: {e}')

    except KeyError as e:
        raise InvalidResponse(f'Failed to get browser ws address: {e}')


def validate_browser_paths(paths: list[str]) -> str:
    """验证潜在的浏览器可执行路径并返回第一个有效路径。

    检查可能的浏览器二进制位置列表以查找现有的、
    可执行浏览器。特定于浏览器的子类使用它来定位
    未提供显式二进制路径时的浏览器可执行文件。

    参数：
        paths：用于检查浏览器可执行文件的潜在文件路径列表。
            这些应该是适合当前操作系统的绝对路径。

    返回：
        str：找到的第一个有效的浏览器可执行路径。

    加薪：
        InvalidBrowserPath：如果在该路径中找不到浏览器可执行文件。"""
    for path in paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    raise InvalidBrowserPath(f'No valid browser path found in: {paths}')


def clean_script_for_analysis(script: str) -> str:
    """通过删除注释和字符串文字来清理 JavaScript 代码。

    这有助于在分析脚本结构时避免误报。

    参数：
        script：要清理的 JavaScript 代码。

    返回：
        str：清理后的脚本，删除了注释和字符串。"""
    #删除行注释
    cleaned = re.sub(r'//.*?$', '', script, flags=re.MULTILINE)
    #删除块注释
    cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)
    #删除双引号字符串
    cleaned = re.sub(r'"[^"]*"', '""', cleaned)
    #删除单引号字符串
    cleaned = re.sub(r"'[^']*'", "''", cleaned)
    #删除模板文字
    cleaned = re.sub(r'`[^`]*`', '``', cleaned)

    return cleaned


def is_script_already_function(script: str) -> bool:
    """检查 JavaScript 脚本是否已包装在函数中。

    参数：
        script：要分析的 JavaScript 代码。

    返回：
        bool：如果 script 已经是一个函数，则为 True，否则为 False。"""
    cleaned_script = clean_script_for_analysis(script)

    function_pattern = r'^\s*function\s*\([^)]*\)\s*\{'
    arrow_function_pattern = r'^\s*\([^)]*\)\s*=>\s*\{'

    return bool(
        re.match(function_pattern, cleaned_script.strip())
        or re.match(arrow_function_pattern, cleaned_script.strip())
    )


def has_return_outside_function(script: str) -> bool:
    """检查 JavaScript 脚本是否在函数之外有 return 语句。

    参数：
        script：要分析的 JavaScript 代码。

    返回：
        bool：如果脚本有 return 外部函数，则为 True，否则为 False。"""
    cleaned_script = clean_script_for_analysis(script)

    #如果已经是一个函数，则无需检查
    if is_script_already_function(cleaned_script):
        return False

    #寻找“返回”语句
    return_pattern = r'\breturn\b'
    if not re.search(return_pattern, cleaned_script):
        return False

    #通过计算大括号的数量来检查 return 是否在函数内部
    lines = cleaned_script.split('\n')
    brace_count = 0
    in_function = False

    for line in lines:
        #检查函数声明
        if re.search(r'\bfunction\b', line) or re.search(r'=>', line):
            in_function = True

        #计算大括号数
        brace_count += line.count('{') - line.count('}')

        #检查退货声明
        if re.search(return_pattern, line):
            if not in_function or brace_count <= 0:
                return True

        #如果我们回到顶层，则重置功能标志
        if brace_count <= 0:
            in_function = False

    return False


def normalize_synthetic_xpath(selector: str) -> str:
    """标准化由构建器生成的合成 XPath 选择器。

    将 //*[@xpath="..."] 形式的选择器转换回原始选择器
    引号之间的 XPath 字符串。如果满足则返回输入不变
    模式不存在或无法安全解析。

    参数：
        选择器：可能包含合成 XPath 格式的选择器字符串。

    返回：
        str：标准化的原始 XPath 或输入选择器（如果未应用标准化）。"""
    s = selector.strip()
    if not s.startswith('//*[@xpath='):
        return selector
    prefix = '//*[@xpath="'
    start_idx = s.find(prefix)
    if start_idx == -1:
        return selector
    start_idx += len(prefix)
    end_idx = s.rfind('"]')
    if end_idx == -1 or end_idx <= start_idx:
        return selector
    return s[start_idx:end_idx]
