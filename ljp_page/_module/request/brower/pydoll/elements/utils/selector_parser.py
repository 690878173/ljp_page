"""选择器解析和构建用于元素查找的实用程序。

集中检查、构建或转换 CSS 和 XPath 的所有逻辑
选择器字符串。这使得 mixin 层专注于编排
（查找元素、管理超时、发出 CDP 命令）
纯粹的字符串操作就在这里。"""

from __future__ import annotations

from ljp_page.logger import loguru_logger
import re
from typing import Optional

from ljp_page._module.request.brower.pydoll.constants import By, Scripts
from ljp_page._module.request.brower.pydoll.utils import normalize_synthetic_xpath



__all__ = ['SelectorParser']

#------------------------------------------------------------------------------------------
#编译模式
#------------------------------------------------------------------------------------------

_IFRAME_XPATH_NODE_RE = re.compile(r'^(?:\w+::)?iframe(?:\[|$)', re.IGNORECASE)
_IFRAME_XPATH_GROUPED_RE = re.compile(r'\biframe\b', re.IGNORECASE)
_CSS_TAG_NAME_RE = re.compile(r'^([a-zA-Z][a-zA-Z0-9-]*)')
_XPATH_PREFIXES: list[tuple[str, int]] = [('.//', 3), ('//', 2), ('./', 2), ('/', 1)]

#嵌套深度跟踪器的查找表
_QUOTE_TRANSITIONS: dict[str, tuple[int, bool]] = {"'": (0, True), '"': (1, True)}
_DEPTH_TRANSITIONS: dict[str, tuple[int, int]] = {
    '[': (0, 1),
    ']': (0, -1),
    '(': (1, 1),
    ')': (1, -1),
}


class SelectorParser:
    """无状态帮助器，用于解析、构建和分类 CSS / XPath 选择器。

    每个方法都是一个“@staticmethod”——该类纯粹用作
    命名空间将解析表面区域保持在一起。 ``查找元素混合``
    在这里委托所有选择器字符串的工作。"""

    #------------------------------------------------------------------
    #表达类型检测
    #------------------------------------------------------------------

    @staticmethod
    def get_expression_type(expression: str) -> By:
        """从表达式语法自动检测选择器类型。

        图案：
        - XPath：以``./``、``/`` 或``(/`` 开头
        - 默认：``By.CSS_SELECTOR``"""
        if expression.startswith(('./', '/', '(/')):
            return By.XPATH
        return By.CSS_SELECTOR

    #------------------------------------------------------------------
    #根据关键字标准构建 XPath
    #------------------------------------------------------------------

    @staticmethod
    def build_xpath(
        id: Optional[str] = None,
        class_name: Optional[str] = None,
        name: Optional[str] = None,
        tag_name: Optional[str] = None,
        text: Optional[str] = None,
        **attributes: str,
    ) -> str:
        """根据多个属性标准构建 XPath 表达式。

        使用“and”组合多个条件构造复杂的 XPath
        运营商。正确处理空格分隔的类的类名
        列表。使用“contains()”进行文本匹配（部分文本支持）。

        注意：
            带下划线的属性名称会自动转换为
            连字符以匹配 HTML 属性命名约定
            （例如“data_test”->“data-test”）。"""
        xpath_conditions: list[str] = []
        base_xpath = f'//{tag_name}' if tag_name else '//*'
        if id:
            xpath_conditions.append(f'@id="{id}"')
        if class_name:
            xpath_conditions.append(
                f'contains(concat(" ", normalize-space(@class), " "), " {class_name} ")'
            )
        if name:
            xpath_conditions.append(f'@name="{name}"')
        if text:
            xpath_conditions.append(f'contains(text(), "{text}")')
        for attribute, value in attributes.items():
            html_attribute = attribute.replace('_', '-')
            xpath_conditions.append(f'@{html_attribute}="{value}"')

        xpath = (
            f'{base_xpath}[{" and ".join(xpath_conditions)}]' if xpath_conditions else base_xpath
        )
        loguru_logger.debug(f'build_xpath() -> {xpath}')
        return xpath

    #------------------------------------------------------------------
    #XPath 助手
    #------------------------------------------------------------------

    @staticmethod
    def ensure_relative_xpath(xpath: str) -> str:
        """如果需要，可以通过在前面添加点来确保 XPath 是相对的。

        将绝对 XPath 转换为相对 XPath 以进行基于上下文的搜索。"""
        return f'.{xpath}' if not xpath.startswith('.') else xpath

    #------------------------------------------------------------------
    #JS 文本表达式生成器
    #------------------------------------------------------------------

    @staticmethod
    def build_text_expression(selector: str, method: str) -> Optional[str]:
        """使用“Scripts”构建 JS 表达式来提取“textContent”
        基于选择器类型。"""
        raw = str(selector)
        method_lc = (method or '').lower()

        if 'xpath' in method_lc:
            normalized_xpath = normalize_synthetic_xpath(raw)
            escaped_xpath = normalized_xpath.replace('"', '\\"')
            return Scripts.GET_TEXT_BY_XPATH.replace('{escaped_value}', escaped_xpath)

        if method_lc == 'name':
            escaped_name = raw.replace('"', '\\"')
            xpath = f'//*[@name="{escaped_name}"]'
            return Scripts.GET_TEXT_BY_XPATH.replace('{escaped_value}', xpath)

        escaped = raw.replace('\\', '\\\\').replace('"', '\\"')
        if method_lc == 'id':
            css = f'#{escaped}'
        elif method_lc == 'class_name':
            css = f'.{escaped}'
        elif method_lc == 'tag_name':
            css = escaped
        else:
            css = escaped
        return Scripts.GET_TEXT_BY_CSS.replace('{selector}', css)

    #------------------------------------------------------------------
    #iframe 交叉：XPath
    #------------------------------------------------------------------

    @staticmethod
    def parse_iframe_segments_xpath(expression: str) -> list[tuple[By, str]]:
        """在 iframe 边界处拆分 XPath 表达式以实现跨 iframe
        遍历。

        将 XPath 解析为由 ``/`` 或 ``//`` 分隔的步骤，尊重
        带引号的字符串、方括号和圆括号。节点测试为的步骤
        “iframe”（不区分大小写）充当分割点：所有内容
        包括iframe步骤成为一段，其余部分
        开始一个以``//`` 为前缀的新段。

        参数：
            表达式：原始 XPath 表达式。

        返回：
            “（By.XPATH，segment）”元组列表。  单元素列表
            当没有检测到 iframe 交叉时。"""
        xpath_steps = SelectorParser._tokenize_xpath_steps(expression)
        if not xpath_steps:
            return [(By.XPATH, expression)]

        iframe_split_indices: list[int] = [
            step_index
            for step_index, (_sep, step_text) in enumerate(xpath_steps)
            if SelectorParser._is_iframe_xpath_step(step_text) and step_index < len(xpath_steps) - 1
        ]

        if not iframe_split_indices:
            return [(By.XPATH, expression)]

        return SelectorParser._build_xpath_segments(xpath_steps, iframe_split_indices)

    #------------------------------------------------------------------
    #iframe 交叉：CSS
    #------------------------------------------------------------------

    @staticmethod
    def parse_iframe_segments_css(expression: str) -> list[tuple[By, str]]:
        """在 iframe 边界处拆分 CSS 选择器以进行跨 iframe 遍历。

        将选择器标记为由以下分隔的复合选择器
        组合符（空格、``>``、``+``、``~``），尊重带引号的字符串，
        方括号和圆括号。标签名称为“iframe”的复合体
        （不区分大小写）充当分割点。

        参数：
            表达式：原始 CSS 选择器。

        返回：
            “（By.CSS_SELECTOR，segment）”元组列表。  单一元素
            未检测到 iframe 交叉时的列表。"""
        css_compounds = SelectorParser._tokenize_css_compounds(expression)
        if not css_compounds:
            return [(By.CSS_SELECTOR, expression)]

        iframe_split_indices: list[int] = [
            compound_index
            for compound_index, (compound_text, _comb) in enumerate(css_compounds)
            if SelectorParser._is_iframe_css_compound(compound_text)
            and compound_index < len(css_compounds) - 1
        ]

        if not iframe_split_indices:
            return [(By.CSS_SELECTOR, expression)]

        return SelectorParser._build_css_segments(css_compounds, iframe_split_indices)

    #=====================================================================
    #私人帮手
    #=====================================================================

    @staticmethod
    def _is_at_nesting_depth_zero(
        char: str,
        quote_state: list[bool],
        depth_state: list[int],
    ) -> bool:
        """跟踪引用/括号/括号嵌套并返回 char 是否位于
        深度 0。就地改变 *quote_state* 和 *depth_state*。"""
        if quote_state[0] or quote_state[1]:
            if quote_state[0]:
                quote_state[0] = char != "'"
            else:
                quote_state[1] = char != '"'
            return False

        if char in _QUOTE_TRANSITIONS:
            index, value = _QUOTE_TRANSITIONS[char]
            quote_state[index] = value
            return False

        if char in _DEPTH_TRANSITIONS:
            index, delta = _DEPTH_TRANSITIONS[char]
            depth_state[index] += delta
            return False

        return depth_state[0] == 0 and depth_state[1] == 0

    #-- XPath 分词器 ----------------------------------------------------------

    @staticmethod
    def _detect_xpath_leading_separator(expression: str) -> tuple[str, int]:
        """返回 XPath 前缀的“(separator, start_index)”。"""
        if expression.startswith('('):
            return '', 0
        for prefix, length in _XPATH_PREFIXES:
            if expression.startswith(prefix):
                return prefix, length
        return '', 0

    @staticmethod
    def _tokenize_xpath_steps(expression: str) -> list[tuple[str, str]]:
        """将 XPath 标记为“(separator, step_text)”对。"""
        xpath_steps: list[tuple[str, str]] = []
        current_separator, token_start = SelectorParser._detect_xpath_leading_separator(expression)
        char_index = token_start
        quote_state = [False, False]
        depth_state = [0, 0]

        while char_index < len(expression):
            char = expression[char_index]
            at_depth_zero = SelectorParser._is_at_nesting_depth_zero(char, quote_state, depth_state)

            if at_depth_zero and char == '/':
                step_text = expression[token_start:char_index]
                if step_text:
                    xpath_steps.append((current_separator, step_text))
                is_double_slash = (
                    char_index + 1 < len(expression) and expression[char_index + 1] == '/'
                )
                current_separator = '//' if is_double_slash else '/'
                char_index += 2 if is_double_slash else 1
                token_start = char_index
                continue
            char_index += 1

        remaining_text = expression[token_start:]
        if remaining_text:
            xpath_steps.append((current_separator, remaining_text))

        return xpath_steps

    @staticmethod
    def _is_iframe_xpath_step(step_text: str) -> bool:
        """返回单个 XPath 步骤的节点测试是否为“iframe”。"""
        if step_text.startswith('('):
            return bool(_IFRAME_XPATH_GROUPED_RE.search(step_text))
        return bool(_IFRAME_XPATH_NODE_RE.match(step_text))

    @staticmethod
    def _build_xpath_segments(
        xpath_steps: list[tuple[str, str]],
        iframe_split_indices: list[int],
    ) -> list[tuple[By, str]]:
        """将 XPath 步骤重新组装成在 iframe 索引处分割的段。"""
        segments: list[tuple[By, str]] = []
        segment_start = 0

        for split_index in iframe_split_indices:
            segment_parts: list[str] = []
            for step_index in range(segment_start, split_index + 1):
                separator, step_text = xpath_steps[step_index]
                if step_index == segment_start and segment_start != 0:
                    segment_parts.append('//' + step_text)
                else:
                    segment_parts.append(separator + step_text)
            segments.append((By.XPATH, ''.join(segment_parts)))
            segment_start = split_index + 1

        if segment_start < len(xpath_steps):
            segment_parts = []
            for step_index in range(segment_start, len(xpath_steps)):
                separator, step_text = xpath_steps[step_index]
                if step_index == segment_start:
                    segment_parts.append('//' + step_text)
                else:
                    segment_parts.append(separator + step_text)
            segments.append((By.XPATH, ''.join(segment_parts)))

        return segments

    #-- CSS 分词器 --------------------------------------------------

    @staticmethod
    def _tokenize_css_compounds(expression: str) -> list[tuple[str, str | None]]:
        """将 CSS 选择器标记为“(compound_text,combinator_after)”对。"""
        css_compounds: list[tuple[str, str | None]] = []
        token_start = 0
        char_index = 0
        quote_state = [False, False]
        depth_state = [0, 0]

        while char_index < len(expression):
            char = expression[char_index]
            at_depth_zero = SelectorParser._is_at_nesting_depth_zero(char, quote_state, depth_state)

            if at_depth_zero and char in ' >+~':
                compound_text = expression[token_start:char_index]
                if not compound_text.strip():
                    char_index += 1
                    continue
                combinator, char_index = SelectorParser._consume_css_combinator(
                    expression, char_index
                )
                css_compounds.append((compound_text, combinator))
                token_start = char_index
                continue
            char_index += 1

        remaining_text = expression[token_start:].strip()
        if remaining_text:
            css_compounds.append((remaining_text, None))

        return css_compounds

    @staticmethod
    def _consume_css_combinator(expression: str, start: int) -> tuple[str, int]:
        """使用 CSS 组合器区域并返回``(combinator, next_index)``。"""
        char_index = start
        while char_index < len(expression) and expression[char_index] == ' ':
            char_index += 1
        if char_index < len(expression) and expression[char_index] in '>+~':
            combinator = expression[char_index]
            char_index += 1
            while char_index < len(expression) and expression[char_index] == ' ':
                char_index += 1
        else:
            combinator = ' '
        return combinator, char_index

    @staticmethod
    def _is_iframe_css_compound(compound_text: str) -> bool:
        """返回 CSS 复合选择器的标签名称是否为“iframe”。"""
        stripped = compound_text.strip()
        if stripped and stripped[0] in '.#[:':
            return False
        match = _CSS_TAG_NAME_RE.match(stripped)
        if not match:
            return False
        return match.group(1).lower() == 'iframe'

    @staticmethod
    def _format_css_combinator(combinator: str) -> str:
        """将 CSS 组合器格式化为人类可读的输出。"""
        if combinator == ' ':
            return ' '
        return f' {combinator} '

    @staticmethod
    def _build_css_segments(
        css_compounds: list[tuple[str, str | None]],
        iframe_split_indices: list[int],
    ) -> list[tuple[By, str]]:
        """将 CSS 复合重新组装成在 iframe 索引处分割的段。"""
        segments: list[tuple[By, str]] = []
        segment_start = 0

        for split_index in iframe_split_indices:
            segment_parts: list[str] = []
            for compound_index in range(segment_start, split_index + 1):
                compound_text, _combinator = css_compounds[compound_index]
                if compound_index > segment_start:
                    previous_combinator = css_compounds[compound_index - 1][1] or ' '
                    segment_parts.append(SelectorParser._format_css_combinator(previous_combinator))
                segment_parts.append(compound_text)
            segments.append((By.CSS_SELECTOR, ''.join(segment_parts)))
            segment_start = split_index + 1

        if segment_start < len(css_compounds):
            segment_parts = []
            for compound_index in range(segment_start, len(css_compounds)):
                compound_text, _combinator = css_compounds[compound_index]
                if compound_index > segment_start:
                    previous_combinator = css_compounds[compound_index - 1][1] or ' '
                    segment_parts.append(SelectorParser._format_css_combinator(previous_combinator))
                segment_parts.append(compound_text)
            segments.append((By.CSS_SELECTOR, ''.join(segment_parts)))

        return segments
