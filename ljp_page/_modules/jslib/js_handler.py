# 04-01-20-12-00
"""JS 执行工具。"""

from __future__ import annotations

import json
import subprocess

import execjs

from .config import JsRuntimeConfig


class Js:
    """执行 JS 代码的通用封装。"""

    def __init__(
        self,
        js_path: str,
        engine: str | None = None,
        config: JsRuntimeConfig | None = None,
    ) -> None:
        cfg = config or JsRuntimeConfig()
        self.js_path = js_path
        self.engine = engine or cfg.engine
        self.encoding = cfg.encoding

        with open(self.js_path, "r", encoding=self.encoding) as file_handle:
            self.js_code = file_handle.read()

        if self.engine == "execjs":
            try:
                self.js_ctx = execjs.compile(self.js_code)
            except Exception as exc:
                raise RuntimeError(f"ExecJS 编译失败: {exc}") from exc

    def call(self, func_name: str, *args: object) -> object:
        """调用 JS 函数。"""
        if self.engine == "execjs":
            try:
                return self.js_ctx.call(func_name, *args)
            except Exception as exc:
                raise RuntimeError(f"JS 调用失败({func_name}): {exc}") from exc
        if self.engine == "node":
            return self._call_with_node_subprocess(func_name, *args)
        raise ValueError(f"不支持的 JS 引擎: {self.engine}")

    def _call_with_node_subprocess(self, func_name: str, *args: object) -> object:
        """使用 node 子进程调用 JS 函数。"""
        args_json = json.dumps(args, ensure_ascii=False)
        wrapper_js = f"""
        {self.js_code}
        try {{
            const args = {args_json};
            const result = {func_name}(...args);
            console.log(JSON.stringify(result));
        }} catch (e) {{
            console.error(e.toString());
            process.exit(1);
        }}
        """

        try:
            result = subprocess.run(
                ["node", "-e", wrapper_js],
                capture_output=True,
                text=True,
                encoding=self.encoding,
                check=True,
            )
            return json.loads(result.stdout.strip())
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"Node 执行失败: {exc.stderr}") from exc
        except Exception as exc:
            raise RuntimeError(f"Node 调用异常: {exc}") from exc


__all__ = ["Js"]
