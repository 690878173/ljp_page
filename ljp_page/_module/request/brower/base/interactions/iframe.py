from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable, Optional

from ljp_page._module.request.brower.pydoll.commands import DomCommands, PageCommands, RuntimeCommands, TargetCommands
from ljp_page._module.request.brower.pydoll.connection import ConnectionHandler
from ljp_page._module.request.brower.pydoll.exceptions import InvalidIFrame
from dom.methods import DescribeNodeResponse, GetFrameOwnerResponse
from dom.types import Node
from page.methods import CreateIsolatedWorldResponse, GetFrameTreeResponse
from page.types import Frame, FrameTree
from runtime.methods import EvaluateResponse
from target.methods import AttachToTargetResponse, GetTargetsResponse

if TYPE_CHECKING:
    from ljp_page._module.request.brower.pydoll.elements.web_element import WebElement




@dataclass
class IFrameContext:
    """iframe 元素的上下文信息。"""

    frame_id: str
    document_url: Optional[str] = None
    execution_context_id: Optional[int] = None
    document_object_id: Optional[str] = None
    session_handler: Optional[ConnectionHandler] = None
    session_id: Optional[str] = None


class IFrameContextResolver:
    """解析 WebElement 的 iframe 上下文。"""

    def __init__(self, element: WebElement):
        self._element = element

    async def resolve(self) -> IFrameContext:
        """解析并返回 iframe 上下文。

        返回：
            IFrameContext 具有frame_id、document_url、execution_context_id、
            OOPIF 目标的 document_object_id 和会话信息。

        加薪：
            InvalidIFrame：如果无法解析 iframe 上下文。"""
        base_handler, base_session_id = self._get_base_session()
        node_info = await self._describe_element_node(base_handler, base_session_id)
        frame_id, document_url, content_frame_id, backend_node_id = self._extract_frame_metadata(
            node_info
        )

        if not frame_id and backend_node_id is not None:
            frame_id, document_url = await self._resolve_frame_by_owner(
                base_handler, base_session_id, backend_node_id, document_url
            )

        session_handler, session_id, frame_id, document_url = await self._resolve_oopif_if_needed(
            frame_id,
            content_frame_id,
            backend_node_id,
            current_document_url=document_url,
            base_handler=base_handler,
            base_session_id=base_session_id,
        )

        if not frame_id:
            raise InvalidIFrame('Unable to resolve frameId for the iframe element')

        context = IFrameContext(frame_id=frame_id, document_url=document_url)

        if session_handler and session_id:
            context.session_handler = session_handler
            context.session_id = session_id

        effective_handler = session_handler or base_handler
        effective_session_id = session_id or base_session_id

        execution_context_id = await self._create_isolated_world_for_frame(
            frame_id, effective_handler, effective_session_id
        )
        context.execution_context_id = execution_context_id

        document_object_id = await self._get_document_object_id(execution_context_id, context)
        context.document_object_id = document_object_id

        return context

    def _get_base_session(self) -> tuple[ConnectionHandler, Optional[str]]:
        """返回路由命令的默认处理程序和会话 ID。"""
        handler = (
            getattr(self._element, '_routing_session_handler', None)
            or self._element._connection_handler
        )
        session_id = getattr(self._element, '_routing_session_id', None)
        return handler, session_id

    async def _describe_element_node(
        self,
        handler: ConnectionHandler,
        session_id: Optional[str],
    ) -> Node:
        """使用给定的处理程序/会话描述 iframe 元素。

        这绕过了``_resolve_routing()``，在之前的
        分辨率，可能会返回 iframe *content* 会话而不是
        元素实际所在的父会话。"""
        command = DomCommands.describe_node(object_id=self._element._object_id)
        if session_id:
            command['sessionId'] = session_id
        response: DescribeNodeResponse = await handler.execute_command(command)
        if 'error' in response:
            return {}
        return response.get('result', {}).get('node', {})

    @staticmethod
    def _extract_frame_metadata(
        node_info: Node,
    ) -> tuple[Optional[str], Optional[str], Optional[str], Optional[int]]:
        """从 DOM 节点信息中提取 iframe 相关元数据。

        返回：
            (frame_id、document_url、content_frame_id、backend_node_id) 的元组。
            ``content_frame_id`` 是由框架*创建*的框架 ID
            ``<iframe>`` 元素（框架所有者上的``node_info['frameId']``
            元素）。  对于同源 iframe，它等于
            ``contentDocument.frameId``;对于 OOPIF ``contentDocument`` 是
            不存在，但“content_frame_id”仍然由浏览器设置。"""
        content_document = node_info.get('contentDocument') or {}
        content_frame_id = node_info.get('frameId')
        backend_node_id = node_info.get('backendNodeId')
        frame_id = content_document.get('frameId')
        document_url = (
            content_document.get('documentURL')
            or content_document.get('baseURL')
            or node_info.get('documentURL')
            or node_info.get('baseURL')
        )
        return frame_id, document_url, content_frame_id, backend_node_id

    async def _resolve_frame_by_owner(
        self,
        base_handler: ConnectionHandler,
        base_session_id: Optional[str],
        backend_node_id: int,
        current_document_url: Optional[str],
    ) -> tuple[Optional[str], Optional[str]]:
        """通过匹配所有者 backend_node_id 解析框架 id 和 URL。"""
        owner_frame_id, owner_url = await self._find_frame_by_owner(
            base_handler, base_session_id, backend_node_id
        )
        if not owner_frame_id:
            return None, current_document_url
        return owner_frame_id, owner_url or current_document_url

    async def _find_frame_by_owner(
        self,
        handler: ConnectionHandler,
        session_id: Optional[str],
        backend_node_id: int,
    ) -> tuple[Optional[str], Optional[str]]:
        """通过匹配所有者 backend_node_id 查找框架。"""
        frame_tree = await self._get_frame_tree_for(handler, session_id)
        for frame_node in self._walk_frames(frame_tree):
            candidate_frame_id = frame_node.get('id', '')
            if not candidate_frame_id:
                continue
            owner_backend_id = await self._owner_backend_for(
                handler, session_id, candidate_frame_id
            )
            if owner_backend_id == backend_node_id:
                return candidate_frame_id, frame_node.get('url')
        return None, None

    @staticmethod
    async def _get_frame_tree_for(
        handler: ConnectionHandler,
        session_id: Optional[str],
    ) -> FrameTree:
        """获取给定连接/目标的页面框架树。"""
        command = PageCommands.get_frame_tree()
        if session_id:
            command['sessionId'] = session_id
        response: GetFrameTreeResponse = await handler.execute_command(command)
        return response['result']['frameTree']

    @staticmethod
    def _walk_frames(tree: FrameTree) -> Iterable[Frame]:
        """递归遍历FrameTree并收集所有帧描述符。"""
        if not tree:
            return []
        frames: list[Frame] = [tree['frame']]
        for child_frame in tree.get('childFrames', []) or []:
            frames.extend(IFrameContextResolver._walk_frames(child_frame))
        return [frame_node for frame_node in frames if frame_node]

    @staticmethod
    async def _owner_backend_for(
        handler: ConnectionHandler,
        session_id: Optional[str],
        frame_id: str,
    ) -> Optional[int]:
        """获取拥有给定框架的 DOM 元素的 backendNodeId。"""
        command = DomCommands.get_frame_owner(frame_id=frame_id)
        if session_id:
            command['sessionId'] = session_id
        response: GetFrameOwnerResponse = await handler.execute_command(command)
        return response.get('result', {}).get('backendNodeId')

    async def _resolve_oopif_if_needed(
        self,
        current_frame_id: Optional[str],
        content_frame_id: Optional[str],
        backend_node_id: Optional[int],
        current_document_url: Optional[str],
        base_handler: Optional[ConnectionHandler] = None,
        base_session_id: Optional[str] = None,
    ) -> tuple[Optional[ConnectionHandler], Optional[str], Optional[str], Optional[str]]:
        """需要时解析 OOPIF 和路由。"""
        if not content_frame_id or (current_frame_id and backend_node_id is None):
            return None, None, current_frame_id, current_document_url

        (
            session_handler,
            session_id,
            resolved_frame_id,
            resolved_url,
        ) = await self._resolve_oopif_by_parent(
            content_frame_id, backend_node_id, base_handler, base_session_id
        )

        if session_handler and session_id and resolved_url:
            return (
                session_handler,
                session_id,
                resolved_frame_id or current_frame_id,
                resolved_url or current_document_url,
            )

        return (
            None,
            None,
            current_frame_id or resolved_frame_id,
            current_document_url or resolved_url,
        )

    async def _resolve_oopif_by_parent(
        self,
        content_frame_id: str,
        backend_node_id: Optional[int],
        base_handler: Optional[ConnectionHandler] = None,
        base_session_id: Optional[str] = None,
    ) -> tuple[Optional[ConnectionHandler], Optional[str], Optional[str], Optional[str]]:
        """使用内容框架 ID 解析进程外 iframe。

        ``content_frame_id`` 是由框架*创建*的框架 ID
        ``<iframe>`` 元素（从 ``DOM.describeNode`` 获得
        ``node.frameId``）。  对于 OOPIF 目标，目标的根框架
        共享这个ID，所以我们可以直接匹配而不需要
        ``DOM.getFrameOwner``。

        当不可能进行直接帧 ID 匹配时（例如嵌套子帧
        在 OOPIF 内部），该方法回退到“DOM.getFrameOwner”
        使用具有 DOM 可见性的路由处理程序/会话
        父上下文。"""
        browser_handler = ConnectionHandler(
            connection_port=self._element._connection_handler._connection_port
        )
        targets_response: GetTargetsResponse = await browser_handler.execute_command(
            TargetCommands.get_targets()
        )
        target_infos = targets_response.get('result', {}).get('targetInfos', [])

        #可以解析 DOM.getFrameOwner 的处理程序/会话
        #元素的上下文。  当 <iframe> 位于嵌套 OOPIF 内时
        #选项卡级处理程序不可见；我们必须通过
        #最初找到该元素的会话。
        owner_handler = base_handler or self._element._connection_handler
        owner_session_id = base_session_id

        direct_children = [
            target_info
            for target_info in target_infos
            if target_info.get('type') in {'iframe', 'page'}
            and target_info.get('parentFrameId') == content_frame_id
        ]

        is_single_child = len(direct_children) == 1
        for child_target in direct_children:
            attach_response: AttachToTargetResponse = await browser_handler.execute_command(
                TargetCommands.attach_to_target(target_id=child_target['targetId'], flatten=True)
            )
            attached_session_id = attach_response.get('result', {}).get('sessionId')
            if not attached_session_id:
                continue

            frame_tree = await self._get_frame_tree_for(browser_handler, attached_session_id)
            root_frame = (frame_tree or {}).get('frame', {})
            root_frame_id = root_frame.get('id', '')

            if is_single_child and root_frame_id and backend_node_id is None:
                return (
                    browser_handler,
                    attached_session_id,
                    root_frame_id,
                    root_frame.get('url'),
                )

            if root_frame_id and backend_node_id is not None:
                owner_backend_id = await self._owner_backend_for(
                    owner_handler, owner_session_id, root_frame_id
                )
                if owner_backend_id == backend_node_id:
                    return (
                        browser_handler,
                        attached_session_id,
                        root_frame_id,
                        root_frame.get('url'),
                    )

        for target_info in target_infos:
            if target_info.get('type') not in {'iframe', 'page'}:
                continue
            attach_response = await browser_handler.execute_command(
                TargetCommands.attach_to_target(
                    target_id=target_info.get('targetId', ''), flatten=True
                )
            )
            attached_session_id = attach_response.get('result', {}).get('sessionId')
            if not attached_session_id:
                continue

            frame_tree = await self._get_frame_tree_for(browser_handler, attached_session_id)
            root_frame = (frame_tree or {}).get('frame', {})
            root_frame_id = root_frame.get('id', '')

            #直接匹配：<iframe>元素的frameId（content_frame_id）
            #等于该目标的根帧 ID。  这处理嵌套的 OOPIF
            #其中 DOM.getFrameOwner 无法通过 main 解析
            #页面处理程序。
            if root_frame_id and root_frame_id == content_frame_id:
                return (
                    browser_handler,
                    attached_session_id,
                    root_frame_id,
                    root_frame.get('url'),
                )

            if root_frame_id and backend_node_id is not None:
                owner_backend_id = await self._owner_backend_for(
                    owner_handler, owner_session_id, root_frame_id
                )
                if owner_backend_id == backend_node_id:
                    return (
                        browser_handler,
                        attached_session_id,
                        root_frame_id,
                        root_frame.get('url'),
                    )

            child_frame_id = self._find_child_by_parent(frame_tree, content_frame_id)
            if child_frame_id:
                return browser_handler, attached_session_id, child_frame_id, None

        return None, None, None, None

    @staticmethod
    def _find_child_by_parent(tree: FrameTree, parent_id: str) -> Optional[str]:
        """查找其parentId等于给定的子框架的id。"""
        if not tree:
            return None
        for child in tree.get('childFrames', []) or []:
            child_frame = child.get('frame', {})
            if child_frame.get('parentId') == parent_id:
                return child_frame.get('id')
            found = IFrameContextResolver._find_child_by_parent(child, parent_id)
            if found:
                return found
        return None

    @staticmethod
    async def _create_isolated_world_for_frame(
        frame_id: str,
        handler: ConnectionHandler,
        session_id: Optional[str],
    ) -> int:
        """为给定的框架创建孤立的世界。"""
        create_command = PageCommands.create_isolated_world(
            frame_id=frame_id,
            world_name=f'pydoll::iframe::{frame_id}',
            grant_universal_access=True,
        )
        if session_id:
            create_command['sessionId'] = session_id
        create_response: CreateIsolatedWorldResponse = await handler.execute_command(create_command)
        execution_context_id = create_response.get('result', {}).get('executionContextId')
        if not execution_context_id:
            raise InvalidIFrame('Unable to create isolated world for iframe')
        return execution_context_id

    async def _get_document_object_id(
        self,
        execution_context_id: int,
        context: IFrameContext,
    ) -> str:
        """获取 iframe 上下文中的 document.documentElement 对象 id。"""
        evaluate_command = RuntimeCommands.evaluate(
            expression='document.documentElement',
            context_id=execution_context_id,
        )
        if context.session_id:
            evaluate_command['sessionId'] = context.session_id

        handler = context.session_handler or self._element._connection_handler
        evaluate_response: EvaluateResponse = await handler.execute_command(evaluate_command)

        result_object = evaluate_response.get('result', {}).get('result', {})
        document_object_id = result_object.get('objectId')
        if not document_object_id:
            raise InvalidIFrame('Unable to obtain document reference for iframe')
        return document_object_id
