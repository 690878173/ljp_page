import execjs
import os
import subprocess
from functools import lru_cache


class Js:
    """
    执行JS代码的通用封装
    支持 execjs 和 nodejs 直接调用
    """

    def __init__(self, js_path, engine='execjs'):
        self.js_path = js_path
        self.engine = engine
        with open(self.js_path, 'r', encoding='utf-8') as f:
            self.js_code = f.read()

        if self.engine == 'execjs':
            try:
                self.js_ctx = execjs.compile(self.js_code)
            except Exception as e:
                raise RuntimeError(f"ExecJS编译失败: {e}. 请检查JS语法或Node环境.")

    def call(self, func_name, *args):
        """调用JS函数"""
        if self.engine == 'execjs':
            try:
                return self.js_ctx.call(func_name, *args)
            except Exception as e:
                # 尝试降级或提供更详细错误
                raise RuntimeError(f"JS调用失败({func_name}): {e}")
        elif self.engine == 'node':
            return self._call_with_node_subprocess(func_name, *args)

    def _call_with_node_subprocess(self, func_name, *args):
        """
        使用subprocess直接调用node执行
        需要JS文件中有对应的导出或自执行逻辑适配，这里仅作为示例扩展
        """
        # 构造一个临时wrapper脚本
        import json
        args_json = json.dumps(args)
        wrapper_js = f"""
        const fs = require('fs');
        // 注入原JS代码
        {self.js_code}

        // 调用目标函数
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
                ['node', '-e', wrapper_js],
                capture_output=True,
                text=True,
                encoding='utf-8',
                check=True
            )
            return json.loads(result.stdout.strip())
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Node执行失败: {e.stderr}")
        except Exception as e:
            raise RuntimeError(f"Node调用异常: {e}")
