from __future__ import annotations

import asyncio
import json
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from ljp_page._module.request.brower.pydoll.commands import InputCommands, RuntimeCommands
from ljp_page._module.request.brower.pydoll.constants import Scripts, ScrollPosition
from ljp_page._module.request.brower.pydoll.interactions.utils import CubicBezier
from input.types import MouseEventType
from runtime.methods import EvaluateResponse

if TYPE_CHECKING:
    from ljp_page._module.request.brower.pydoll.browser.tab import Tab


@dataclass(frozen=True)
class ScrollTimingConfig:
    """真实滚动物理的配置。"""

    min_duration: float = 0.5
    max_duration: float = 1.5

    bezier_points: tuple[float, float, float, float] = (0.645, 0.045, 0.355, 1.0)

    frame_interval: float = 0.012

    delta_jitter: int = 3

    micro_pause_probability: float = 0.05
    micro_pause_min: float = 0.02
    micro_pause_max: float = 0.05

    overshoot_probability: float = 0.15
    overshoot_factor_min: float = 1.02
    overshoot_factor_max: float = 1.08


class Scroll:
    """用于控制页面滚动行为的 API。

    提供向不同方向滚动页面的方法，
    到特定位置，或相对距离。支持人性化
    通过逼真的物理模拟滚动。"""

    def __init__(
        self,
        tab: Tab,
        timing: Optional[ScrollTimingConfig] = None,
    ):
        """使用 Tab 实例初始化 Scroll。

        参数：
            tab：执行滚动命令的选项卡实例。
            定时：可选自定义定时配置，实现人性化滚动。"""
        self._tab = tab
        self._timing = timing or ScrollTimingConfig()

    async def by(
        self,
        position: ScrollPosition,
        distance: int | float,
        smooth: bool = True,
        humanize: bool = False,
    ):
        """将页面沿指定方向滚动相对距离。

        参数：
            位置：滚动方向（上、下、左、右）。
            distance：要滚动的像素数。
            smooth：如果为 True，则使用平滑滚动动画；如果为 False，则使用即时滚动动画。
            humanize：模拟具有动量和惯性的类人滚动。"""
        if humanize:
            await self._scroll_humanized(position, distance)
            return

        axis, scroll_distance = self._get_axis_and_distance(position, distance)
        behavior = self._get_behavior(smooth)

        script = Scripts.SCROLL_BY.format(
            axis=axis,
            distance=scroll_distance,
            behavior=behavior,
        )

        await self._execute_script_await_promise(script)

    async def to_top(self, smooth: bool = True, humanize: bool = False):
        """滚动到页面顶部 (Y=0)。

        参数：
            smooth：如果为 True，则使用平滑滚动动画；如果为 False，则使用即时滚动动画。
            humanize：模拟具有动量和惯性的类人滚动。"""
        if humanize:
            await self._scroll_to_end_humanized(ScrollPosition.UP)
            return

        behavior = self._get_behavior(smooth)
        script = Scripts.SCROLL_TO_TOP.format(behavior=behavior)
        await self._execute_script_await_promise(script)

    async def to_bottom(self, smooth: bool = True, humanize: bool = False):
        """滚动到页面底部（Y=document.body.scrollHeight）。

        参数：
            smooth：如果为 True，则使用平滑滚动动画；如果为 False，则使用即时滚动动画。
            humanize：模拟具有动量和惯性的类人滚动。"""
        if humanize:
            await self._scroll_to_end_humanized(ScrollPosition.DOWN)
            return

        behavior = self._get_behavior(smooth)
        script = Scripts.SCROLL_TO_BOTTOM.format(behavior=behavior)
        await self._execute_script_await_promise(script)

    async def _scroll_to_end_humanized(self, position: ScrollPosition):
        """通过多个类似人类的轻拂滚动到顶部或底部。

        人类不会通过一次动作滚动数千个像素 - 他们会这样做
        多个滚动手势，中间有短暂的停顿。"""
        max_flick_distance = random.uniform(600, 1200)
        min_remaining_threshold = 30
        min_stuck_threshold = 5
        min_flick_distance = 100

        #卡住滚动的故障保护
        last_remaining = float('inf')
        stuck_counter = 0
        max_stuck_attempts = 10

        while True:
            if position == ScrollPosition.DOWN:
                remaining = await self._get_remaining_scroll_to_bottom()
            else:
                remaining = await self._get_current_scroll_y()

            if remaining <= min_remaining_threshold:
                break

            #检查我们是否被卡住了
            has_progressed = abs(remaining - last_remaining) >= min_stuck_threshold

            if has_progressed:
                stuck_counter = 0

            if not has_progressed:
                stuck_counter += 1
                if stuck_counter >= max_stuck_attempts:
                    break

            last_remaining = remaining

            flick_distance = min(remaining, max_flick_distance)
            if flick_distance < min_flick_distance and remaining > min_flick_distance:
                flick_distance = min_flick_distance

            await self._scroll_humanized(position, flick_distance)

            pause = random.uniform(0.05, 0.15)
            await asyncio.sleep(pause)

            max_flick_distance = random.uniform(600, 1200)

    async def _scroll_humanized(self, position: ScrollPosition, target_distance: float):
        """以逼真的类人物理原理进行滚动。

        模拟基于动量的滚动：
        - 平滑的减速曲线
        - 可变帧间隔
        - 滚动增量中的随机抖动
        - 偶尔出现微停顿
        - 可选的超调和校正"""
        is_vertical = position in {ScrollPosition.UP, ScrollPosition.DOWN}
        direction = -1 if position in {ScrollPosition.UP, ScrollPosition.LEFT} else 1

        effective_distance = self._calculate_effective_distance(target_distance)
        duration = self._calculate_duration(effective_distance)

        scrolled_so_far = await self._perform_scroll_loop(
            effective_distance, duration, is_vertical, direction
        )

        if effective_distance > target_distance and scrolled_so_far > target_distance:
            correction_distance = scrolled_so_far - target_distance
            correction_direction = -direction

            await asyncio.sleep(random.uniform(0.1, 0.2))

            await self._scroll_correction(
                is_vertical=is_vertical,
                direction=correction_direction,
                distance=correction_distance,
            )

    async def _perform_scroll_loop(
        self,
        effective_distance: float,
        duration: float,
        is_vertical: bool,
        direction: int,
    ) -> float:
        """使用贝塞尔计时执行主滚动循环。"""
        timing = self._timing
        bezier = CubicBezier(*timing.bezier_points)

        start_time = asyncio.get_running_loop().time()
        current_time = 0.0
        scrolled_so_far = 0.0

        while current_time < duration:
            now = asyncio.get_running_loop().time()
            current_time = now - start_time

            if current_time >= duration:
                break

            progress = current_time / duration
            eased_progress = bezier.solve(progress)

            target_pos = effective_distance * eased_progress
            delta = target_pos - scrolled_so_far

            jitter = random.randint(-timing.delta_jitter, timing.delta_jitter)
            delta += jitter

            delta = max(delta, 0)

            if delta >= 1:
                await self._dispatch_scroll_event(
                    delta_x=0 if is_vertical else int(delta * direction),
                    delta_y=int(delta * direction) if is_vertical else 0,
                )
                scrolled_so_far += delta

            frame_delay = timing.frame_interval + random.uniform(-0.002, 0.002)
            await asyncio.sleep(frame_delay)

            if random.random() < timing.micro_pause_probability:
                pause_duration = random.uniform(timing.micro_pause_min, timing.micro_pause_max)
                await asyncio.sleep(pause_duration)
                start_time += pause_duration

        return scrolled_so_far

    def _calculate_effective_distance(self, target_distance: float) -> float:
        """计算有效距离，包括超调。"""
        timing = self._timing
        should_overshoot = random.random() < timing.overshoot_probability
        overshoot_factor = (
            random.uniform(timing.overshoot_factor_min, timing.overshoot_factor_max)
            if should_overshoot
            else 1.0
        )
        return target_distance * overshoot_factor

    def _calculate_duration(self, distance: float) -> float:
        """根据距离计算滚动持续时间。"""
        timing = self._timing
        base_duration = random.uniform(timing.min_duration, timing.max_duration)
        duration = base_duration * (1 + 0.2 * (distance / 1000))
        return min(duration, 3.0)

    async def _scroll_correction(self, is_vertical: bool, direction: int, distance: float):
        """超调后进行小幅修正滚动。"""
        timing = self._timing
        scrolled = 0.0

        min_correction_velocity = (distance * (0.15)) / timing.frame_interval
        correction_velocity = random.uniform(
            max(200, min_correction_velocity), max(400, min_correction_velocity * 1.5)
        )

        while scrolled < distance:
            frame_delta = correction_velocity * timing.frame_interval
            frame_delta = min(frame_delta, distance - scrolled)

            await self._dispatch_scroll_event(
                delta_x=0 if is_vertical else int(frame_delta * direction),
                delta_y=int(frame_delta * direction) if is_vertical else 0,
            )

            scrolled += frame_delta
            correction_velocity *= 0.85

            await asyncio.sleep(timing.frame_interval)

    async def _dispatch_scroll_event(self, delta_x: int, delta_y: int):
        """调度鼠标滚轮事件以进行滚动。"""
        viewport = await self._get_viewport_center()
        command = InputCommands.dispatch_mouse_event(
            type=MouseEventType.MOUSE_WHEEL,
            x=viewport[0],
            y=viewport[1],
            delta_x=delta_x,
            delta_y=delta_y,
        )
        await self._tab._execute_command(command)

    async def _get_viewport_center(self) -> tuple[int, int]:
        """获取视口的中心坐标。"""
        command = RuntimeCommands.evaluate(expression=Scripts.GET_VIEWPORT_CENTER)
        result: EvaluateResponse = await self._tab._execute_command(command)

        value_str = result.get('result', {}).get('result', {}).get('value', '[]')
        expected_dimensions = 2
        try:
            value = json.loads(value_str)
            if value and isinstance(value, list) and len(value) == expected_dimensions:
                return (int(value[0]), int(value[1]))
        except (json.JSONDecodeError, TypeError):
            pass
        return (400, 300)

    async def _get_current_scroll_y(self) -> float:
        """获取当前垂直滚动位置。"""
        command = RuntimeCommands.evaluate(expression=Scripts.GET_SCROLL_Y)
        result: EvaluateResponse = await self._tab._execute_command(command)
        return float(result.get('result', {}).get('result', {}).get('value', 0))

    async def _get_remaining_scroll_to_bottom(self) -> float:
        """获取滚动到底部的剩余距离。"""
        command = RuntimeCommands.evaluate(expression=Scripts.GET_REMAINING_SCROLL_TO_BOTTOM)
        result: EvaluateResponse = await self._tab._execute_command(command)
        return float(result.get('result', {}).get('result', {}).get('value', 0))

    @staticmethod
    def _get_axis_and_distance(
        position: ScrollPosition, distance: int | float
    ) -> tuple[str, int | float]:
        """将滚动位置转换为轴和有符号距离。

        参数：
            位置：滚动方向。
            distance：滚动的绝对距离。

        返回：
            (axis,signed_distance) 的元组，其中轴为“左”或“上”
            signed_distance 根据方向为正或负。"""
        if position in {ScrollPosition.UP, ScrollPosition.DOWN}:
            axis = 'top'
            scroll_distance = -distance if position == ScrollPosition.UP else distance
            return axis, scroll_distance

        axis = 'left'
        scroll_distance = -distance if position == ScrollPosition.LEFT else distance
        return axis, scroll_distance

    @staticmethod
    def _get_behavior(smooth: bool) -> str:
        """将 smooth 布尔值转换为 CSS 滚动行为值。

        参数：
            smooth：是否使用平滑滚动。

        返回：
            如果 smooth 为 True，则为“smooth”，否则为“auto”。"""
        return 'smooth' if smooth else 'auto'

    async def _execute_script_await_promise(self, script: str):
        """执行 JavaScript 并等待承诺解决。

        参数：
            script：返回 Promise 的 JavaScript 代码。"""
        command = RuntimeCommands.evaluate(expression=script, await_promise=True)
        return await self._tab._execute_command(command)


#向后兼容别名
ScrollAPI = Scroll
