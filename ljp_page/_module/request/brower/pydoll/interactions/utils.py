from __future__ import annotations

import math
import random


class CubicBezier:
    """三次贝塞尔曲线解算器可实现平滑的动画计时。

    基于 WebKit/Chromium 的 UnitBezier。映射时间进度值
    使用三次贝塞尔曲线调整为缓和进度值。"""

    def __init__(self, point1_x: float, point1_y: float, point2_x: float, point2_y: float):
        self.coefficient_c_x = 3.0 * point1_x
        self.coefficient_b_x = 3.0 * (point2_x - point1_x) - self.coefficient_c_x
        self.coefficient_a_x = 1.0 - self.coefficient_c_x - self.coefficient_b_x

        self.coefficient_c_y = 3.0 * point1_y
        self.coefficient_b_y = 3.0 * (point2_y - point1_y) - self.coefficient_c_y
        self.coefficient_a_y = 1.0 - self.coefficient_c_y - self.coefficient_b_y

    def sample_curve_x(self, time_progress: float) -> float:
        return (
            (self.coefficient_a_x * time_progress + self.coefficient_b_x) * time_progress
            + self.coefficient_c_x
        ) * time_progress

    def sample_curve_y(self, time_progress: float) -> float:
        return (
            (self.coefficient_a_y * time_progress + self.coefficient_b_y) * time_progress
            + self.coefficient_c_y
        ) * time_progress

    def sample_curve_derivative_x(self, time_progress: float) -> float:
        return (
            3.0 * self.coefficient_a_x * time_progress + 2.0 * self.coefficient_b_x
        ) * time_progress + self.coefficient_c_x

    def solve_curve_x(self, target_x: float, epsilon: float = 1e-6) -> float:
        """给定 x 值，找到相应的 t 值。"""
        estimated_t = target_x

        for _ in range(8):
            current_x = self.sample_curve_x(estimated_t) - target_x
            if abs(current_x) < epsilon:
                return estimated_t
            derivative = self.sample_curve_derivative_x(estimated_t)
            if abs(derivative) < epsilon:
                break
            estimated_t -= current_x / derivative

        lower_bound = 0.0
        upper_bound = 1.0
        estimated_t = target_x

        if estimated_t < lower_bound:
            return lower_bound
        if estimated_t > upper_bound:
            return upper_bound

        while lower_bound < upper_bound:
            current_x = self.sample_curve_x(estimated_t)
            if abs(current_x - target_x) < epsilon:
                return estimated_t
            if target_x > current_x:
                lower_bound = estimated_t
            else:
                upper_bound = estimated_t
            estimated_t = (upper_bound - lower_bound) * 0.5 + lower_bound

        return estimated_t

    def solve(self, input_x: float) -> float:
        """获取给定 x（时间进度）的 y 值。"""
        return self.sample_curve_y(self.solve_curve_x(input_x))


def minimum_jerk(t: float) -> float:
    """[0,1] 中标准化时间 t 处的最小加加速度位置。

    返回 10t^3 - 15t^4 + 6t^5，产生钟形速度
    轮廓：缓慢开始，中间高峰，缓慢结束。"""
    t2 = t * t
    t3 = t2 * t
    return 10.0 * t3 - 15.0 * t3 * t + 6.0 * t3 * t2


def bezier_2d(
    t: float,
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
) -> tuple[float, float]:
    """计算参数 t 处的二维三次贝塞尔曲线。

    B(t) = (1-t)^3*P0 + 3(1-t)^2*t*P1 + 3(1-t)*t^2*P2 + t^3*P3"""
    u = 1.0 - t
    u2 = u * u
    u3 = u2 * u
    t2 = t * t
    t3 = t2 * t
    x = u3 * p0[0] + 3.0 * u2 * t * p1[0] + 3.0 * u * t2 * p2[0] + t3 * p3[0]
    y = u3 * p0[1] + 3.0 * u2 * t * p1[1] + 3.0 * u * t2 * p2[1] + t3 * p3[1]
    return (x, y)


def fitts_duration(
    distance: float,
    target_width: float,
    a: float,
    b: float,
) -> float:
    """菲茨定律：MT = a + b * log2(D/W + 1)。"""
    if distance <= 0:
        return a
    return a + b * math.log2(distance / target_width + 1.0)


def random_control_points(
    start: tuple[float, float],
    end: tuple[float, float],
    curvature_min: float,
    curvature_max: float,
    curvature_asymmetry: float,
    short_distance_threshold: float,
) -> tuple[tuple[float, float], tuple[float, float]]:
    """为弯曲的鼠标路径生成随机 2D Bezier 控制点。

    控制点垂直于起点线偏移。
    第一个控制点沿路径较早偏置
    （弹道相位不对称）。"""
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    distance = math.hypot(dx, dy)

    if distance < 1.0:
        return (start, end)

    perp = (-dy / distance, dx / distance)

    scale = min(1.0, distance / short_distance_threshold)
    offsets = (
        random.uniform(curvature_min, curvature_max) * distance * scale,
        random.uniform(curvature_min, curvature_max) * distance * scale,
    )

    sign = random.choice([-1.0, 1.0])
    t1 = random.uniform(0.2, curvature_asymmetry)
    t2 = random.uniform(curvature_asymmetry, 0.8)

    cp1 = (
        start[0] + dx * t1 + perp[0] * offsets[0] * sign,
        start[1] + dy * t1 + perp[1] * offsets[0] * sign,
    )

    counter = random.uniform(0.3, 1.0)
    cp2 = (
        start[0] + dx * t2 + perp[0] * offsets[1] * sign * counter,
        start[1] + dy * t2 + perp[1] * offsets[1] * sign * counter,
    )

    return (cp1, cp2)
