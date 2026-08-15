from typing import Any, Iterator


class DOM:
    # NOTE 将 CDP 节点的 attributes 列表转换为字典
    @staticmethod
    def attrs(node: dict[str, Any]) -> dict[str, str]:
        """将 CDP 节点的 attributes 列表转换为字典。"""
        raw_attrs = node.get("attributes", [])
        return {
            str(raw_attrs[i]): str(raw_attrs[i + 1])
            for i in range(0, len(raw_attrs) - 1, 2)
        }
    # NOTE 判断当前节点自身信息是否包含目标域名"
    @classmethod
    def has_targe_domain(cls, node: dict[str, Any], DOMAIN) -> bool:
        """判断当前节点自身信息是否包含目标域名。"""
        attrs = cls.attrs(node)
        values = [
            node.get("documentURL", ""),
            node.get("baseURL", ""),
            node.get("frameId", ""),
            *attrs.values(),
        ]
        return bool(DOMAIN) and any(DOMAIN in str(value) for value in values)
    # NOTE 深度遍历 DOM、iframe 文档和 shadow root，并保留目标子树状态。
    @classmethod
    def _iter_nodes(cls, node: dict[str, Any], *, in_targe_tree: bool = False, ) -> Iterator[tuple[dict[str, Any], bool]]:
        """深度遍历 DOM、iframe 文档和 shadow root，并保留目标子树状态。"""
        current_in_targe = in_targe_tree or cls.has_targe_domain(node)
        yield node, current_in_targe

        content_document = node.get("contentDocument")
        if content_document:
            yield from cls._iter_nodes(content_document, in_targe_tree=current_in_targe)

        for key in ("shadowRoots", "templateContent", "children"):
            children = node.get(key)
            if isinstance(children, dict):
                yield from cls._iter_nodes(children, in_targe_tree=current_in_targe)
                continue
            for child in children or []:
                yield from cls._iter_nodes(child, in_targe_tree=current_in_targe)
    # NOTE 找所有影子根，only_one仅返回找到的第一个
    @classmethod
    def find_shadow_roots(cls, root: dict[str, Any], only_one: bool = False, *, deep: bool = False, ) -> list[dict[str, Any]] | dict[str, Any] | None:
        """查找 DOM 树中的 shadow root。"""
        shadow_roots: list[dict[str, Any]] = []
        seen: set[int] = set()

        def walk(node: dict[str, Any], in_shadow: bool = False) -> dict[str, Any] | None:
            for shadow_root in node.get("shadowRoots", []) or []:
                shadow_id = id(shadow_root)
                if shadow_id not in seen and (deep or not in_shadow):
                    seen.add(shadow_id)
                    if only_one:
                        return shadow_root
                    shadow_roots.append(shadow_root)

                found = walk(shadow_root, in_shadow=True)
                if found is not None:
                    return found

            content_document = node.get("contentDocument")
            if content_document:
                found = walk(content_document, in_shadow=in_shadow)
                if found is not None:
                    return found

            for child in node.get("children", []) or []:
                found = walk(child, in_shadow=in_shadow)
                if found is not None:
                    return found

            return None

        found_root = walk(root)
        if only_one:
            return found_root
        return shadow_roots
    # NOTE 判断 CDP 节点是否为目标复选框元素,目标span且class属性为指定属性
    @classmethod
    def _is_checkbox_node(cls, node: dict[str, Any], checkbox_class: str) -> bool:
        """判断 CDP 节点是否为目标复选框元素。"""
        attrs = cls.attrs(node)
        class_names = attrs.get("class", "").split()
        local_name = str(node.get("localName", "")).lower()
        return local_name == "span" and checkbox_class in class_names
    # NOTE 在当前 DOM 树中直接查找复选框节点
    @classmethod
    def find_checkbox(cls, root: dict[str, Any], checkbox_class, targe: bool = False) -> dict[str, Any] | None:
        """在当前 DOM 树中直接查找复选框节点。"""
        for node, in_targe_tree in cls._iter_nodes(root):
            if targe and not in_targe_tree:
                continue
            if cls._is_checkbox_node(node=node, checkbox_class=checkbox_class):
                return node
        return None

    @staticmethod
    def _collect_shadow_roots_from_tree(node: Node, results: list[tuple[Node, int | None]]) -> None:
        """Recursively walk a DOM tree collecting shadow root entries."""
        host_backend_id = node.get('backendNodeId')
        for shadow_root in node.get('shadowRoots', []):
            results.append((shadow_root, host_backend_id))
            DOM._collect_shadow_roots_from_tree(shadow_root, results)

        for child in node.get('children', []):
            DOM._collect_shadow_roots_from_tree(child, results)

        content_doc = node.get('contentDocument')
        if content_doc:
            DOM._collect_shadow_roots_from_tree(content_doc, results)