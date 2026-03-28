# 项目结构梳理（2026-03-28）

## 重构结论

本轮已完成两件事：

1. 去掉历史 `_ljp_*` 前缀目录，统一为语义化目录名。  
2. 不保留旧兼容层，全部代码导入切换到新路径。

## 当前目录结构（核心）

```text
ljp_page/
├─ core/              # 核心基础层（基类 / 中间件 / 适配器）
├─ modules/           # 业务模块层（request / captcha / playwright）
├─ applications/      # 应用层（pc / jwxt）
├─ runtime/           # 异步调度与执行器
├─ config/            # 配置系统
├─ foundation/        # 基础类与通用异常
├─ data_analysis/     # 数据分析能力
├─ utils/             # 通用工具
├─ ui/                # UI 相关
├─ jslib/             # JS 工具
└─ sjfx/              # 对 data_analysis 的便捷入口
```

## 目录改名映射

- `_ljp_app` -> `applications`
- `_ljp_async` -> `runtime`
- `_ljp_config` -> `config`
- `_ljp_coro` -> `foundation`
- `_ljp_data_analysis` -> `data_analysis`
- `_ljp_js` -> `jslib`
- `_ljp_ui` -> `ui`
- `_ljp_utils` -> `utils`

## 说明

- 旧 `_ljp_*` 目录已移除，不再保留兼容导入。
- 中间件与适配器已归位到 `core/`：
  - `core/middleware/http_middleware.py`
  - `core/adapters/http_transport.py`
- 请求模块位于 `modules/request/`，并有模块基类 `modules/request/base.py`。
- 验证码与 Playwright 模块也已补齐基类并迁移至 `modules/`。
