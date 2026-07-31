from __future__ import annotations

import ast
import os
import sys
from importlib import import_module
from pathlib import Path
from typing import Callable, Iterable, Literal

# 全局缓存池，避免同一个懒加载成员被反复导入。
GLOBAL_MOD_CACHE: dict[str, dict[str, object]] = {}
GLOBAL_EXPORT_CACHE: dict[str, dict[str, str]] = {}


def scan_export_modules(pkg_path: str, include_private: bool = False) -> list[str]:
    """扫描当前包下可导出的非私有 py 文件与子包。

    参数:
        pkg_path: 当前包所在目录。
        include_private: 是否包含以下划线开头的私有模块。
    返回值:
        list[str]: 可参与懒加载的模块名称列表。
    """

    res: list[str] = []
    for name in sorted(os.listdir(pkg_path)):
        if name == "__pycache__":
            continue
        stem = name[:-3] if name.endswith(".py") else name
        if not include_private and stem.startswith("_"):
            continue

        full = os.path.join(pkg_path, name)
        if os.path.isdir(full):
            if os.path.exists(os.path.join(full, "__init__.py")):
                res.append(name)
        elif name.endswith(".py") and name != "__init__.py":
            res.append(stem)
    return res


def make_submodule_getattr(pkg_name: str, mod_list: list[str]) -> Callable[[str], object]:
    """生成“只导出子模块名”的懒加载入口。"""

    cache = GLOBAL_MOD_CACHE.setdefault(pkg_name, {})

    def _getattr(name: str) -> object:
        if name in cache:
            return cache[name]
        if name not in mod_list:
            raise AttributeError(f"{pkg_name} 没有成员 {name}")
        mod = import_module(f"{pkg_name}.{name}")
        cache[name] = mod
        return mod

    return _getattr


def make_entity_getattr(pkg_name: str, mod_list: list[str]) -> Callable[[str], object]:
    """生成“直接导出子模块内部类/函数”的懒加载入口。"""

    cache = GLOBAL_MOD_CACHE.setdefault(pkg_name, {})
    export_map = _build_export_map(pkg_name, mod_list)

    def _getattr(name: str) -> object:
        if name in cache:
            return cache[name]

        mod_name = export_map.get(name)
        if mod_name is not None:
            sub_mod = import_module(f"{pkg_name}.{mod_name}")
            obj = getattr(sub_mod, name)
            cache[name] = obj
            return obj

        # 允许按属性访问直接子模块，例如 package.submodule。
        if name in mod_list:
            sub_mod = import_module(f"{pkg_name}.{name}")
            cache[name] = sub_mod
            return sub_mod

        raise AttributeError(f"{pkg_name} 找不到成员 {name}")

    return _getattr


def make_proxy_getattr(target_module: str, export_names: Iterable[str]) -> Callable[[str], object]:
    """生成代理模块的懒加载入口，用于公开壳模块转发内部实现。"""

    exports = list(export_names)
    export_set = set(exports)
    cache = GLOBAL_MOD_CACHE.setdefault(target_module, {})

    def _getattr(name: str) -> object:
        if name in cache:
            return cache[name]
        if name not in export_set:
            raise AttributeError(f"{target_module} 没有成员 {name}")
        mod = import_module(target_module)
        obj = getattr(mod, name)
        cache[name] = obj
        return obj

    return _getattr


def proxy_module_exports(
    target_module: str,
    export_names: Iterable[str],
) -> tuple[Callable[[str], object], list[str]]:
    """为壳模块生成 `__getattr__` 与 `__all__`。"""

    exports = list(export_names)
    return make_proxy_getattr(target_module, exports), exports


def mapped_module_exports(
    export_map: dict[str, str],
) -> tuple[Callable[[str], object], list[str]]:
    """为来自多个目标模块的成员生成懒加载入口。"""

    exports = list(export_map)
    cache_key = "mapped:" + "|".join(f"{name}={module}" for name, module in export_map.items())
    cache = GLOBAL_MOD_CACHE.setdefault(cache_key, {})

    def _getattr(name: str) -> object:
        if name in cache:
            return cache[name]
        target_module = export_map.get(name)
        if target_module is None:
            raise AttributeError(f"找不到成员 {name}")
        mod = import_module(target_module)
        obj = getattr(mod, name)
        cache[name] = obj
        return obj

    return _getattr, exports


def bind_lazy_exports(
    pkg_name: str,
    file_path: str,
    *,
    mode: Literal["entity", "submodule"] = "entity",
    include_private: bool = False,
) -> tuple[Callable[[str], object], list[str]]:
    """按当前包路径一次性绑定懒加载入口与导出列表。

    参数:
        pkg_name: 当前包名，通常传入 `__name__`。
        file_path: 当前 `__init__.py` 的 `__file__`。
        mode: `entity` 导出子模块内成员，`submodule` 只导出子模块。
        include_private: 是否允许扫描以下划线开头的私有模块。
    返回值:
        tuple[Callable[[str], object], list[str]]: `__getattr__` 与 `__all__`。
    """

    pkg_path = str(Path(file_path).parent)
    mod_list = scan_export_modules(pkg_path, include_private=include_private)
    if mode == "submodule":
        return make_submodule_getattr(pkg_name, mod_list), mod_list
    return make_entity_getattr(pkg_name, mod_list), merge_all_export(pkg_name, mod_list)


def merge_all_export(pkg_name: str, mod_list: list[str]) -> list[str]:
    """静态合并所有子模块 `__all__`，不在生成导出列表时导入重模块。"""

    return list(_build_export_map(pkg_name, mod_list).keys())


def _build_export_map(pkg_name: str, mod_list: list[str]) -> dict[str, str]:
    cache_key = f"{pkg_name}:{','.join(mod_list)}"
    if cache_key in GLOBAL_EXPORT_CACHE:
        return GLOBAL_EXPORT_CACHE[cache_key]

    pkg_dir = _resolve_package_dir(pkg_name)
    export_map: dict[str, str] = {}
    for mod_name in mod_list:
        mod_path = _module_path(pkg_dir, mod_name)
        for export_name in _collect_export_names(mod_path):
            export_map.setdefault(export_name, mod_name)

    GLOBAL_EXPORT_CACHE[cache_key] = export_map
    return export_map


def _resolve_package_dir(pkg_name: str) -> Path:
    mod = sys.modules.get(pkg_name)
    if mod is not None:
        mod_file = getattr(mod, "__file__", None)
        if mod_file:
            return Path(mod_file).parent
        mod_path = getattr(mod, "__path__", None)
        if mod_path:
            return Path(next(iter(mod_path)))
    return Path(import_module(pkg_name).__file__).parent


def _module_path(pkg_dir: Path, mod_name: str) -> Path:
    package_path = pkg_dir / mod_name
    if package_path.is_dir():
        return package_path
    return pkg_dir / f"{mod_name}.py"


def _collect_export_names(mod_path: Path) -> list[str]:
    if mod_path.is_dir():
        init_path = mod_path / "__init__.py"
        literal_all = _read_literal_all(init_path)
        if literal_all is not None:
            return literal_all

        names: list[str] = []
        for child_name in scan_export_modules(str(mod_path)):
            child_path = _module_path(mod_path, child_name)
            names.extend(_collect_export_names(child_path))
        return names

    return _read_literal_all(mod_path) or []


def _read_literal_all(file_path: Path) -> list[str] | None:
    if not file_path.exists():
        return None

    tree = ast.parse(file_path.read_text(encoding="utf-8-sig"))
    for node in tree.body:
        value_node: ast.AST | None = None
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets):
                value_node = node.value
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == "__all__":
                value_node = node.value

        if value_node is None:
            continue
        try:
            value = ast.literal_eval(value_node)
        except (ValueError, SyntaxError):
            return None
        if isinstance(value, (list, tuple)) and all(isinstance(item, str) for item in value):
            return list(value)
        return None
    return None




__all__ = ['bind_lazy_exports','proxy_module_exports','mapped_module_exports']
