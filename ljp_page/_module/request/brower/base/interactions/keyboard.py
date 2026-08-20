from __future__ import annotations

import asyncio
from ljp_page.logger import loguru_logger
import random
import warnings
from dataclasses import dataclass
from typing import Any, Optional, Protocol, cast

from ljp_page._module.request.brower.pydoll.commands import InputCommands
from ljp_page._module.request.brower.pydoll.constants import (
    CHAR_TO_KEY_INFO,
    DEFAULT_TYPO_PROBABILITY,
    QWERTY_NEIGHBORS,
    Key,
    TypoType,
)
from input.types import KeyEventType, KeyModifier



class CommandExecutor(Protocol):
    """可以执行 CDP 命令的对象的协议。"""

    async def _execute_command(self, command: Any) -> Any: ...


@dataclass(frozen=True)
class TypoResult:
    """打字错误生成的结果。"""

    typo_type: TypoType
    wrong_char: str = ''


@dataclass(frozen=True)
class TimingConfig:
    """真实打字计时的配置。"""

    keystroke_min: float = 0.03
    keystroke_max: float = 0.12
    punctuation_min: float = 0.08
    punctuation_max: float = 0.18
    thinking_probability: float = 0.02
    thinking_min: float = 0.3
    thinking_max: float = 0.7
    distraction_probability: float = 0.005
    distraction_min: float = 0.5
    distraction_max: float = 1.2
    mistake_realize_min: float = 0.1
    mistake_realize_max: float = 0.25
    after_correction_min: float = 0.03
    after_correction_max: float = 0.08
    double_press_min: float = 0.02
    double_press_max: float = 0.05
    hesitation_min: float = 0.15
    hesitation_max: float = 0.3


@dataclass(frozen=True)
class TypoConfig:
    """拼写错误生成权重的配置。"""

    adjacent_weight: float = 0.55
    transpose_weight: float = 0.20
    double_weight: float = 0.12
    skip_weight: float = 0.08
    missed_space_weight: float = 0.05


class Keyboard:
    """Tab 和 WebElement 的键盘输入控制器。

    提供以下方法：
    - Tab：公共键盘模拟（按、下、上、热键）
    - WebElement：带有可选人性化功能的私人文本输入"""

    PAUSE_CHARS = frozenset(' .,!?;:\n')

    def __init__(
        self,
        executor: CommandExecutor,
        timing: Optional[TimingConfig] = None,
        typo_config: Optional[TypoConfig] = None,
    ):
        """初始化键盘控制器。

        参数：
            执行器：具有 _execute_command 方法的对象（Tab 或 WebElement）。
            计时：可选的自定义计时配置。
            typo_config：可选的自定义拼写错误权重配置。"""
        self._executor = executor
        self._timing = timing or TimingConfig()
        self._typo_config = typo_config or TypoConfig()
        self._has_focus = hasattr(executor, 'focus')

    async def _ensure_focus(self):
        """如果执行器元素支持焦点，则在击键之前重新聚焦它。"""
        if self._has_focus:
            await self._executor.focus()

    async def press(
        self,
        key: Key,
        modifiers: Optional[KeyModifier] = None,
        interval: float = 0.1,
    ):
        """按下并释放一个键（向下 + 等待 + 向上）。

        参数：
            key：要按下的键（来自 Key 枚举）。
            修饰符：可选的键修饰符（Alt=1、Ctrl=2、Meta=4、Shift=8）。
            间隔：按住按键的时间（以秒为单位）。

        示例：
            等待 tab.keyboard.press(Key.ENTER)
            等待 tab.keyboard.press(Key.A, 修饰符=KeyModifier.CTRL)"""
        loguru_logger.info(f'Pressing key: {key} with modifiers: {modifiers}')
        await self.down(key, modifiers)
        await asyncio.sleep(interval)
        await self.up(key)

    async def down(self, key: Key, modifiers: Optional[KeyModifier] = None):
        """按下某个键（不释放）。

        参数：
            key：按下的键（来自 Key 枚举）。
            修饰符：可选的键修饰符。"""
        key_name, code = key
        loguru_logger.debug(f'Key down: {key_name}')
        command = InputCommands.dispatch_key_event(
            type=KeyEventType.KEY_DOWN,
            key=key_name,
            windows_virtual_key_code=code,
            native_virtual_key_code=code,
            modifiers=modifiers,
        )
        await self._executor._execute_command(command)

    async def up(self, key: Key):
        """释放按键（按键事件）。

        参数：
            key：释放的键（来自 Key 枚举）。"""
        key_name, code = key
        loguru_logger.debug(f'Key up: {key_name}')
        command = InputCommands.dispatch_key_event(
            type=KeyEventType.KEY_UP,
            key=key_name,
            windows_virtual_key_code=code,
            native_virtual_key_code=code,
        )
        await self._executor._execute_command(command)

    async def hotkey(self, key1: Key, key2: Key, key3: Optional[Key] = None):
        """执行最多 3 个键的组合键（热键）。

        参数：
            key1：第一个键（通常是 Ctrl、Shift、Alt 等修饰键）。
            key2：第二个键。
            key3：可选的第三个键。

        示例：
            等待 tab.keyboard.hotkey(Key.CONTROL, Key.C) # Ctrl+C"""
        loguru_logger.info(f'Hotkey: {key1} + {key2}' + (f' + {key3}' if key3 else ''))
        keys = [key1, key2]
        if key3 is not None:
            keys.append(key3)

        modifiers, non_modifiers = self._split_modifiers_and_keys(keys)
        modifier_value = self._calculate_modifier_value(modifiers)

        for key in non_modifiers:
            await self.down(key, modifiers=modifier_value)
            await asyncio.sleep(0.05)

        await asyncio.sleep(0.1)

        for key in reversed(non_modifiers):
            await self.up(key)
            await asyncio.sleep(0.05)

    async def type_text(
        self,
        text: str,
        humanize: bool = False,
        interval: Optional[float] = None,
    ):
        """逐个字符地键入文本。

        参数：
            文本：要输入的文本。
            humanize：当为 True 时，模拟类似人类的打字
                可变的延迟和偶尔的拼写错误（~2%）。
            间隔：已弃用。使用 humanize=True 代替。

        示例：
            等待 tab.keyboard.type_text("Hello World", humanize=True)
            等待 tab.keyboard.type_text("Hello World")"""
        if interval is not None:
            warnings.warn(
                'The "interval" parameter is deprecated and will be removed '
                'in a future version. Use "humanize=True" for realistic typing.',
                DeprecationWarning,
                stacklevel=2,
            )

        if humanize:
            await self._type_text_humanized(text)
            return

        for current_char in text:
            await self._type_char(current_char)
            await asyncio.sleep(0.05)

    async def _type_text_humanized(self, text: str):
        """以逼真的类人行为输入文本。"""
        char_index = 0
        while char_index < len(text):
            current_char = text[char_index]
            next_char = text[char_index + 1] if char_index + 1 < len(text) else None

            should_skip_next = await self._process_char_with_typo(current_char, next_char)

            if should_skip_next:
                char_index += 1

            await self._apply_realistic_delay(current_char)
            char_index += 1

    async def _type_char(self, char: str):
        """键入单个字符，在每次击键之前重新聚焦该元素。"""
        await self._ensure_focus()
        key, code, keycode = CHAR_TO_KEY_INFO.get(char, (char, '', 0))
        command_down = InputCommands.dispatch_key_event(
            type=KeyEventType.KEY_DOWN,
            key=key,
            code=code,
            text=char,
            unmodified_text=char,
            windows_virtual_key_code=keycode,
            native_virtual_key_code=keycode,
        )
        await self._executor._execute_command(command_down)

        command_up = InputCommands.dispatch_key_event(
            type=KeyEventType.KEY_UP,
            key=key,
            code=code,
            windows_virtual_key_code=keycode,
            native_virtual_key_code=keycode,
        )
        await self._executor._execute_command(command_up)

    async def _type_backspace(self):
        """发送退格键。"""
        await self._ensure_focus()
        await self.down(Key.BACKSPACE)
        await self.up(Key.BACKSPACE)

    async def _process_char_with_typo(
        self,
        current_char: str,
        next_char: Optional[str],
    ) -> bool:
        """处理字符，可能存在拼写错误。如果应该跳过 next，则返回 True。"""
        if not self._should_make_typo():
            await self._type_char(current_char)
            return False

        typo = self._generate_typo(current_char, next_char)
        return await self._handle_typo(current_char, next_char, typo)

    async def _handle_typo(
        self,
        current_char: str,
        next_char: Optional[str],
        typo: TypoResult,
    ) -> bool:
        """处理错字。如果应跳过下一个字符，则返回 True。"""
        if typo.typo_type == TypoType.ADJACENT:
            await self._do_adjacent_typo(current_char, typo.wrong_char)
            return False

        if typo.typo_type == TypoType.TRANSPOSE and next_char:
            await self._do_transpose_typo(current_char, next_char)
            return True

        if typo.typo_type == TypoType.DOUBLE:
            await self._do_double_typo(current_char)
            return False

        if typo.typo_type == TypoType.SKIP:
            await self._do_skip_typo(current_char)
            return False

        if typo.typo_type == TypoType.MISSED_SPACE and current_char == ' ' and next_char:
            await self._do_missed_space_typo(current_char, next_char)
            return True

        await self._type_char(current_char)
        return False

    async def _do_adjacent_typo(self, correct_char: str, wrong_char: str):
        """输入错误的相邻键，暂停，退格，纠正。"""
        timing = self._timing
        await self._type_char(wrong_char)
        await asyncio.sleep(random.uniform(timing.mistake_realize_min, timing.mistake_realize_max))
        await self._type_backspace()
        await asyncio.sleep(
            random.uniform(timing.after_correction_min, timing.after_correction_max)
        )
        await self._type_char(correct_char)

    async def _do_transpose_typo(self, current_char: str, next_char: str):
        """以错误的顺序键入字符，然后修复。"""
        timing = self._timing
        await self._type_char(next_char)
        await asyncio.sleep(random.uniform(timing.keystroke_min, timing.keystroke_max))
        await self._type_char(current_char)

        await asyncio.sleep(random.uniform(timing.mistake_realize_min, timing.mistake_realize_max))
        await self._type_backspace()
        await self._type_backspace()
        await asyncio.sleep(
            random.uniform(timing.after_correction_min, timing.after_correction_max)
        )

        await self._type_char(current_char)
        await asyncio.sleep(random.uniform(timing.keystroke_min, timing.keystroke_max))
        await self._type_char(next_char)

    async def _do_double_typo(self, current_char: str):
        """输入字符两次，然后退格。"""
        timing = self._timing
        await self._type_char(current_char)
        await asyncio.sleep(random.uniform(timing.double_press_min, timing.double_press_max))
        await self._type_char(current_char)
        await asyncio.sleep(random.uniform(timing.mistake_realize_min, timing.mistake_realize_max))
        await self._type_backspace()

    async def _do_skip_typo(self, current_char: str):
        """犹豫一下，然后正常打字。"""
        timing = self._timing
        await asyncio.sleep(random.uniform(timing.hesitation_min, timing.hesitation_max))
        await self._type_char(current_char)

    async def _do_missed_space_typo(self, space_char: str, next_char: str):
        """缺少空格，输入下一个字符，意识到，返回并修复。"""
        timing = self._timing
        await self._type_char(next_char)
        await asyncio.sleep(random.uniform(timing.mistake_realize_min, timing.mistake_realize_max))
        await self._type_backspace()
        await asyncio.sleep(
            random.uniform(timing.after_correction_min, timing.after_correction_max)
        )
        await self._type_char(space_char)
        await asyncio.sleep(
            random.uniform(timing.after_correction_min, timing.after_correction_max)
        )
        await self._type_char(next_char)

    async def _apply_realistic_delay(self, typed_char: str):
        """输入字符后应用真实的延迟。"""
        timing = self._timing
        delay = random.uniform(timing.keystroke_min, timing.keystroke_max)

        if typed_char in self.PAUSE_CHARS:
            delay += random.uniform(timing.punctuation_min, timing.punctuation_max)

        if random.random() < timing.thinking_probability:
            delay += random.uniform(timing.thinking_min, timing.thinking_max)

        if random.random() < timing.distraction_probability:
            delay += random.uniform(timing.distraction_min, timing.distraction_max)

        await asyncio.sleep(delay)

    @staticmethod
    def _should_make_typo() -> bool:
        """确定是否会出现拼写错误。"""
        return random.random() < DEFAULT_TYPO_PROBABILITY

    def _generate_typo(self, current_char: str, next_char: Optional[str]) -> TypoResult:
        """根据 QWERTY 布局生成真实的拼写错误。"""
        typo_type = self._select_typo_type()
        return self._create_typo(typo_type, current_char, next_char)

    def _select_typo_type(self) -> TypoType:
        """根据权重选择拼写错误类型。"""
        config = self._typo_config
        typo_types = [
            TypoType.ADJACENT,
            TypoType.TRANSPOSE,
            TypoType.DOUBLE,
            TypoType.SKIP,
            TypoType.MISSED_SPACE,
        ]
        typo_weights = [
            config.adjacent_weight,
            config.transpose_weight,
            config.double_weight,
            config.skip_weight,
            config.missed_space_weight,
        ]
        return random.choices(typo_types, weights=typo_weights, k=1)[0]

    def _create_typo(
        self,
        typo_type: TypoType,
        current_char: str,
        next_char: Optional[str],
    ) -> TypoResult:
        """根据类型创建拼写错误结果。"""
        typo_handlers = {
            TypoType.ADJACENT: lambda: self._create_adjacent_typo(current_char),
            TypoType.TRANSPOSE: lambda: self._create_transpose_typo(current_char, next_char),
            TypoType.MISSED_SPACE: lambda: self._create_missed_space_typo(current_char),
            TypoType.DOUBLE: lambda: TypoResult(typo_type=TypoType.DOUBLE, wrong_char=current_char),
            TypoType.SKIP: lambda: TypoResult(typo_type=TypoType.SKIP),
        }
        handler = typo_handlers.get(typo_type, typo_handlers[TypoType.SKIP])
        return handler()

    def _create_transpose_typo(self, current_char: str, next_char: Optional[str]) -> TypoResult:
        """创建转置拼写错误，如果不可能，则退回到相邻的位置。"""
        if next_char and next_char.isalpha():
            return TypoResult(typo_type=TypoType.TRANSPOSE, wrong_char=next_char)
        return self._create_adjacent_typo(current_char)

    def _create_missed_space_typo(self, current_char: str) -> TypoResult:
        """创建丢失的空格拼写错误，如果不是空格，则回退到相邻的空格。"""
        if current_char == ' ':
            return TypoResult(typo_type=TypoType.MISSED_SPACE)
        return self._create_adjacent_typo(current_char)

    @staticmethod
    def _create_adjacent_typo(original_char: str) -> TypoResult:
        """创建相邻的键拼写错误。"""
        lowercase_char = original_char.lower()

        if lowercase_char not in QWERTY_NEIGHBORS:
            return TypoResult(typo_type=TypoType.DOUBLE, wrong_char=original_char)

        adjacent_char = random.choice(QWERTY_NEIGHBORS[lowercase_char])

        if original_char.isupper():
            adjacent_char = adjacent_char.upper()

        return TypoResult(typo_type=TypoType.ADJACENT, wrong_char=adjacent_char)

    @staticmethod
    def _split_modifiers_and_keys(keys: list[Key]) -> tuple[list[Key], list[Key]]:
        """将键分为修饰符和非修饰符。"""
        modifier_keys = {Key.CONTROL, Key.SHIFT, Key.ALT, Key.META}
        modifiers = [key for key in keys if key in modifier_keys]
        non_modifiers = [key for key in keys if key not in modifier_keys]
        return modifiers, non_modifiers

    @staticmethod
    def _calculate_modifier_value(modifiers: list[Key]) -> Optional[KeyModifier]:
        """根据修饰键计算 KeyModifier 值。"""
        if not modifiers:
            return None

        modifier_map = {
            Key.ALT: 1,
            Key.CONTROL: 2,
            Key.META: 4,
            Key.SHIFT: 8,
        }

        value = sum(modifier_map.get(mod, 0) for mod in modifiers)
        return cast(KeyModifier, value) if value > 0 else None


KeyboardAPI = Keyboard
