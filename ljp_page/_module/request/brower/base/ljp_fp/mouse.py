from __future__ import annotations

import asyncio
import math
import random
from dataclasses import dataclass
from typing import Optional

from ljp_page._module.request.brower.base.commands import InputCommands, RuntimeCommands
from ljp_page._module.request.brower.base.interactions.utils import (
    bezier_2d,
    fitts_duration,
    minimum_jerk,
    random_control_points,
)
from ljp_page._module.request.brower.base.protocol.input.types import MouseButton, MouseEventType



@dataclass(frozen=True)
class MouseTimingConfig:
    """逼真的鼠标移动物理配置。"""

    fitts_a: float = 0.070
    fitts_b: float = 0.150

    frame_interval: float = 0.012
    frame_interval_variance: float = 0.004

    curvature_min: float = 0.10
    curvature_max: float = 0.30
    curvature_asymmetry: float = 0.6

    short_distance_threshold: float = 50.0

    tremor_amplitude: float = 1.0

    overshoot_probability: float = 0.70
    overshoot_distance_min: float = 0.03
    overshoot_distance_max: float = 0.12
    overshoot_speed_threshold: float = 200.0

    pre_click_pause_min: float = 0.05
    pre_click_pause_max: float = 0.20
    click_hold_min: float = 0.05
    click_hold_max: float = 0.15
    double_click_interval_min: float = 0.05
    double_click_interval_max: float = 0.10
    drag_start_pause_min: float = 0.08
    drag_start_pause_max: float = 0.20
    drag_end_pause_min: float = 0.05
    drag_end_pause_max: float = 0.15

    micro_pause_probability: float = 0.03
    micro_pause_min: float = 0.015
    micro_pause_max: float = 0.04

    min_duration: float = 0.08
    max_duration: float = 2.5


class Mouse:
    """具有真实人性化模拟的鼠标输入控制器。

    提供鼠标移动、单击、双击、
    并使用贝塞尔曲线进行可选的人性化模拟拖动，
    菲茨法则计时、最小加加速度速度曲线、生理学
    颤抖和超调校正。"""

    _DEBUG_INIT_JS = """
    (() => {
        if (document.getElementById('__pydoll_mouse_debug')) return;
        const canvas = document.createElement('canvas');
        canvas.id = '__pydoll_mouse_debug';
        canvas.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;'
            + 'pointer-events:none;z-index:2147483647;';
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        document.body.appendChild(canvas);
        window.__pydoll_debug_ctx = canvas.getContext('2d');
    })();
    """

    _DEBUG_DOT_JS = """
    (() => {{
        const ctx = window.__pydoll_debug_ctx;
        if (!ctx) return;
        ctx.beginPath();
        ctx.arc({x}, {y}, {radius}, 0, 2 * Math.PI);
        ctx.fillStyle = '{color}';
        ctx.fill();
    }})();
    """

    def __init__(
        self,
        tab, # 需要具备 _execute_command方法
        timing: Optional[MouseTimingConfig] = None,
        debug: bool = False,
    ):
        """初始化鼠标控制器。

        参数：
            tab：执行鼠标命令的选项卡实例。
            计时：可选自定义计时配置，实现人性化运动。
            调试：在页面上绘制彩色点以可视化鼠标路径。"""
        self._tab = tab
        self._timing = timing or MouseTimingConfig()
        self._position: tuple[float, float] = (0.0, 0.0)
        self._debug = debug
        self._debug_initialized = False

    @property
    def timing(self) -> MouseTimingConfig:
        """当前的人性化运动计时配置。"""
        return self._timing

    @timing.setter
    def timing(self, config: MouseTimingConfig) -> None:
        """更换定时配置。

        参数：
            config：新的 MouseTimingConfig 用于将来的操作。"""
        self._timing = config

    @property
    def debug(self) -> bool:
        """是否在页面上绘制调试点。"""
        return self._debug

    @debug.setter
    def debug(self, value: bool) -> None:
        """设置是否在页面上绘制调试点。"""
        self._debug = value
        self._debug_initialized = False

    async def move(
        self,
        x: float,
        y: float,
        *,
        humanize: bool = False,
    ) -> None:
        """将鼠标光标移动到指定位置。

        参数：
            x：目标 X 坐标（CSS 像素）。
            y：目标 Y 坐标（CSS 像素）。
            人性化：以自然时序模拟类似人类的曲线运动。"""
        if humanize:
            await self._move_humanized(x, y)
            return

        await self._dispatch_move(x, y)

    async def click(
        self,
        x: float,
        y: float,
        *,
        button: MouseButton = MouseButton.LEFT,
        click_count: int = 1,
        humanize: bool = False,
    ) -> None:
        """单击指定位置。

        参数：
            x：目标 X 坐标（CSS 像素）。
            y：目标 Y 坐标（CSS 像素）。
            按钮：用于单击的鼠标按钮。
            click_count：点击次数（双击为 2）。
            人性化：模拟类人的运动和点击时间。"""
        if humanize:
            await self._click_humanized(x, y, button, click_count)
            return

        await self._dispatch_move(x, y)
        await self._dispatch_button(MouseEventType.MOUSE_PRESSED, button, click_count)
        await self._dispatch_button(MouseEventType.MOUSE_RELEASED, button, click_count)

    async def double_click(
        self,
        x: float,
        y: float,
        *,
        button: MouseButton = MouseButton.LEFT,
        humanize: bool = False,
    ) -> None:
        """在指定位置双击。

        参数：
            x：目标 X 坐标（CSS 像素）。
            y：目标 Y 坐标（CSS 像素）。
            按钮：用于单击的鼠标按钮。
            人性化：模拟类人的运动和点击时间。"""
        await self.click(x, y, button=button, click_count=2, humanize=humanize)

    async def down(self, button: MouseButton = MouseButton.LEFT) -> None:
        """在当前位置按下鼠标按钮。

        参数：
            按钮：按下的鼠标按钮。"""
        await self._dispatch_button(MouseEventType.MOUSE_PRESSED, button)

    async def up(self, button: MouseButton = MouseButton.LEFT) -> None:
        """在当前位置释放鼠标按钮。

        参数：
            按钮：要释放的鼠标按钮。"""
        await self._dispatch_button(MouseEventType.MOUSE_RELEASED, button)

    async def drag(
        self,
        start_x: float,
        start_y: float,
        end_x: float,
        end_y: float,
        *,
        humanize: bool = False,
    ) -> None:
        """从一个位置拖动到另一位置。

        参数：
            start_x：起始X坐标。
            start_y：起始Y坐标。
            end_x：结束 X 坐标。
            end_y：结束 Y 坐标。
            humanize：模拟类似人类的拖动运动。"""
        if humanize:
            await self._drag_humanized(start_x, start_y, end_x, end_y)
            return

        await self._dispatch_move(start_x, start_y)
        await self._dispatch_button(MouseEventType.MOUSE_PRESSED, MouseButton.LEFT)
        await self._dispatch_move(end_x, end_y)
        await self._dispatch_button(MouseEventType.MOUSE_RELEASED, MouseButton.LEFT)

    async def _move_humanized(self, target_x: float, target_y: float) -> None:
        """通过逼真的曲线路径、定时、颤抖和超调来移动鼠标。"""
        start = self._position
        target = (target_x, target_y)
        distance = math.hypot(target_x - start[0], target_y - start[1])

        if distance < 1.0:
            await self._dispatch_move(target_x, target_y)
            return

        config = self._timing
        duration = fitts_duration(distance, 20.0, config.fitts_a, config.fitts_b)
        duration = max(config.min_duration, min(duration, config.max_duration))

        should_overshoot = (
            distance > config.overshoot_speed_threshold
            and random.random() < config.overshoot_probability
        )

        if should_overshoot:
            await self._move_with_overshoot(start, target, duration)
        else:
            cp1, cp2 = self._get_control_points(start, target)
            await self._perform_movement_loop(start, target, duration, cp1, cp2)

        await self._dispatch_move(target_x, target_y)

    async def _move_with_overshoot(
        self,
        start: tuple[float, float],
        target: tuple[float, float],
        duration: float,
    ) -> None:
        """执行超出目标的动作，然后进行纠正。"""
        config = self._timing
        overshoot_fraction = random.uniform(
            config.overshoot_distance_min, config.overshoot_distance_max
        )
        dx = target[0] - start[0]
        dy = target[1] - start[1]
        overshoot = (target[0] + dx * overshoot_fraction, target[1] + dy * overshoot_fraction)

        cp1, cp2 = self._get_control_points(start, overshoot)
        await self._perform_movement_loop(start, overshoot, duration * 0.85, cp1, cp2)

        cp1, cp2 = self._get_control_points(overshoot, target)
        await self._perform_movement_loop(overshoot, target, duration * 0.15, cp1, cp2)

    async def _perform_movement_loop(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        duration: float,
        cp1: tuple[float, float],
        cp2: tuple[float, float],
    ) -> None:
        """使用贝塞尔路径和最小加加速度执行逐帧运动循环。"""
        config = self._timing
        loop = asyncio.get_running_loop()
        start_time = loop.time()
        prev = (start[0], start[1], start_time)

        while True:
            now = loop.time()
            elapsed = now - start_time

            if elapsed >= duration:
                break

            t = minimum_jerk(elapsed / duration)
            x, y = bezier_2d(t, start, cp1, cp2, end)

            sigma = self._compute_tremor_sigma(x, y, now, prev, config)
            x += random.gauss(0, sigma)
            y += random.gauss(0, sigma)

            await self._dispatch_move(x, y)
            prev = (x, y, now)

            frame_delay = config.frame_interval + random.uniform(
                -config.frame_interval_variance, config.frame_interval_variance
            )
            await asyncio.sleep(max(0.001, frame_delay))

            if random.random() < config.micro_pause_probability:
                pause = random.uniform(config.micro_pause_min, config.micro_pause_max)
                await asyncio.sleep(pause)
                start_time += pause

    @staticmethod
    def _compute_tremor_sigma(
        x: float,
        y: float,
        now: float,
        prev: tuple[float, float, float],
        config: MouseTimingConfig,
    ) -> float:
        """计算与光标速度成反比的震颤幅度。"""
        dt = now - prev[2]
        if dt > 0:
            velocity = math.hypot(x - prev[0], y - prev[1]) / dt
            speed_factor = max(0.2, 1.0 - velocity / 500.0)
        else:
            speed_factor = 1.0
        return config.tremor_amplitude * speed_factor

    async def _click_humanized(
        self,
        x: float,
        y: float,
        button: MouseButton,
        click_count: int,
    ) -> None:
        """以真实的动作和时机点击。"""
        config = self._timing

        await self._move_humanized(x, y)

        pre_pause = random.uniform(config.pre_click_pause_min, config.pre_click_pause_max)
        await asyncio.sleep(pre_pause)

        for i in range(click_count):
            current_count = i + 1
            await self._dispatch_button(MouseEventType.MOUSE_PRESSED, button, current_count)

            hold = random.uniform(config.click_hold_min, config.click_hold_max)
            await asyncio.sleep(hold)

            await self._dispatch_button(MouseEventType.MOUSE_RELEASED, button, current_count)

            if current_count < click_count:
                interval = random.uniform(
                    config.double_click_interval_min,
                    config.double_click_interval_max,
                )
                await asyncio.sleep(interval)

    async def _drag_humanized(
        self,
        start_x: float,
        start_y: float,
        end_x: float,
        end_y: float,
    ) -> None:
        """通过逼真的移动、暂停和计时进行拖动。"""
        config = self._timing

        await self._move_humanized(start_x, start_y)
        await self._dispatch_button(MouseEventType.MOUSE_PRESSED, MouseButton.LEFT)

        drag_start_pause = random.uniform(config.drag_start_pause_min, config.drag_start_pause_max)
        await asyncio.sleep(drag_start_pause)

        start = self._position
        distance = math.hypot(end_x - start[0], end_y - start[1])
        duration = fitts_duration(distance, 20.0, config.fitts_a, config.fitts_b)
        duration = max(config.min_duration, min(duration, config.max_duration))

        cp1, cp2 = self._get_control_points(start, (end_x, end_y))
        await self._perform_movement_loop(start, (end_x, end_y), duration, cp1, cp2)
        await self._dispatch_move(end_x, end_y)

        drag_end_pause = random.uniform(config.drag_end_pause_min, config.drag_end_pause_max)
        await asyncio.sleep(drag_end_pause)

        await self._dispatch_button(MouseEventType.MOUSE_RELEASED, MouseButton.LEFT)

    def _get_control_points(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
    ) -> tuple[tuple[float, float], tuple[float, float]]:
        """使用当前计时配置生成贝塞尔曲线控制点。"""
        config = self._timing
        return random_control_points(
            start,
            end,
            config.curvature_min,
            config.curvature_max,
            config.curvature_asymmetry,
            config.short_distance_threshold,
        )

    async def _dispatch_move(self, x: float, y: float) -> None:
        """调度 mouseMoved 事件并更新内部位置。"""
        command = InputCommands.dispatch_mouse_event(
            type=MouseEventType.MOUSE_MOVED,
            x=int(round(x)),
            y=int(round(y)),
        )
        await self._tab._execute_command(command)
        self._position = (x, y)

        if self._debug:
            await self._debug_draw_dot(x, y, radius=2, color='rgba(0,150,255,0.6)')

    async def _dispatch_button(
        self,
        event_type: MouseEventType,
        button: MouseButton,
        click_count: int = 1,
    ) -> None:
        """在当前位置调度 mousePressed 或 mouseReleased。"""
        command = InputCommands.dispatch_mouse_event(
            type=event_type,
            x=int(round(self._position[0])),
            y=int(round(self._position[1])),
            button=button,
            click_count=click_count,
        )
        await self._tab._execute_command(command)

        if self._debug and event_type == MouseEventType.MOUSE_PRESSED:
            await self._debug_draw_dot(
                self._position[0], self._position[1], radius=6, color='rgba(255,50,50,0.9)'
            )

    async def _debug_draw_dot(self, x: float, y: float, radius: int, color: str) -> None:
        """在页面覆盖画布上绘制一个调试点。"""
        if not self._debug_initialized:
            await self._tab._execute_command(RuntimeCommands.evaluate(self._DEBUG_INIT_JS))
            self._debug_initialized = True

        script = self._DEBUG_DOT_JS.format(
            x=int(round(x)), y=int(round(y)), radius=radius, color=color
        )
        await self._tab._execute_command(RuntimeCommands.evaluate(script))


MouseAPI = Mouse
