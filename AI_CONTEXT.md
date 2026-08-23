# AI Context Index

本文件是项目的 AI 上下文入口。处理某个模块前，先读取该模块目录内最近的
`AI_CONTEXT.md`，只在需要实现细节时再读取源码。

| 模块 | 上下文文档 | 用途 |
| --- | --- | --- |
| 任务调度 | `ljp_page/_module/runtime/AI_CONTEXT.md` | `LJPExc`、任务句柄、并发与关闭 |
| HTTP Session | `ljp_page/_module/request/session/AI_CONTEXT.md` | Adapter Session、同步/异步池、验证门 |
| 浏览器自动化 | `ljp_page/_module/request/brower/AI_CONTEXT.md` | Playwright、CDP、页面内 Fetch、cookies/headers、challenge 能力 |

## 维护规则

- 修改模块的公开 API、配置字段、生命周期、职责边界或关键行为时，同一变更必须更新该模块的 `AI_CONTEXT.md`。
- 文档只记录稳定的使用方式、边界和决策；不复制私有实现、逐行逻辑或临时调试信息。
- 文档与源码冲突时，以源码和测试为准，并在该次修改中修正文档。
- 新增有独立公开入口或复杂状态的模块时，在模块目录添加 `AI_CONTEXT.md`，并把路径登记到本索引。

## AI 阅读顺序

1. 先读本文件确认模块范围。
2. 读取目标模块的 `AI_CONTEXT.md`，只读取与当前任务相关的章节。
3. 仅当文档无法回答具体实现、边界条件或测试位置时，再搜索源码。
4. 完成修改后，检查本索引和对应模块文档是否仍准确。

文档用于减少重复探索，不替代类型标注、测试和源码审查。涉及跨模块调用时，分别读取两个
模块的上下文文档，不根据旧调用方反推新模块 API。
