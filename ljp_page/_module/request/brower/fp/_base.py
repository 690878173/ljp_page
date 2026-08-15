
import asyncio
import contextlib
from typing import Optional, TYPE_CHECKING

from ljp_page._module.request.brower.pydoll.protocol.base import T_CommandResponse, Command, T_CommandParams
from ljp_page.logger import logger
from ljp_page._module.request.brower.base.connection import ConnectionHandler
from ljp_page._module.request.brower.base.elements.web_element import WebElement
from ljp_page._module.request.brower.base.interactions import IFrameContext, MouseAPI
from ljp_page._module.request.brower.base.protocol.target.methods import GetTargetsResponse, AttachToTargetResponse
from ljp_page._module.request.brower.base.protocol.target.types import TargetInfo




from ljp_page._module.request.brower.base.elements.shadow_root import ShadowRoot
from ljp_page._module.request.brower.base.exceptions import WaitElementTimeout,CommandExecutionTimeout,WebSocketConnectionClosed
from ljp_page._module.request.brower.base.commands import (
    DomCommands,
    FetchCommands,
    NetworkCommands,
    StorageCommands,
    TargetCommands,
)
from ljp_page._module.request.brower.base.protocol.dom.types import Node, ShadowRootType
from ljp_page._module.request.brower.base.elements.mixins.find_elements_mixin import FindElementsMixin

if TYPE_CHECKING:
    from ljp_page._module.request.brower.base.protocol.dom.methods import (
            DescribeNodeResponse,
            GetDocumentResponse,
            ResolveNodeResponse,
        )


_CLOUDFLARE_CHALLENGE_DOMAIN = 'challenges.cloudflare.com'
_CLOUDFLARE_IFRAME_SELECTOR = f'iframe[src*="{_CLOUDFLARE_CHALLENGE_DOMAIN}"]'
_CLOUDFLARE_CHECKBOX_SELECTOR = 'input[type="checkbox"]'





class _ts(FindElementsMixin):
    def __init__(self):
        self._mouse: MouseAPI = MouseAPI(self)
        self._connection_port : Optional[int] = None


    async def _execute_command(
        self, command: Command):
        pass
    async def _bypass_cloudflare(
        self,
        event: dict,
        time_to_wait_captcha: float = 5,
    ) -> None:
        """Attempt to bypass Cloudflare Turnstile captcha via shadow root traversal.

        Polls for the challenge widget and clicks its checkbox, retrying the
        whole traversal until *time_to_wait_captcha* elapses. Retrying is
        required because Cloudflare injects the widget after the load event and
        re-renders the challenge iframe during its proof-of-work, which
        invalidates any node captured mid-traversal.
        """

        loop = asyncio.get_event_loop()
        deadline = loop.time() + time_to_wait_captcha
        last_error: Optional[Exception] = None
        while True:
            try:
                shadow_root = await self._find_cloudflare_shadow_root()
                if shadow_root is not None:
                    await self._click_cloudflare_checkbox(shadow_root)
                    return
            except Exception as exc:
                last_error = exc
                logger.debug(f'Cloudflare bypass attempt failed, retrying: {exc}')

            if loop.time() >= deadline:
                break
            await asyncio.sleep(0.5)

        if last_error is not None:
            logger.error(f'Error in cloudflare bypass: {last_error}')



    async def _find_cloudflare_shadow_root(self) -> Optional[ShadowRoot]:
        """Return the Cloudflare Turnstile shadow root if currently present.

        Performs a single scan of the page's shadow roots and returns the first
        one whose ``inner_html`` references ``challenges.cloudflare.com``, or
        ``None`` when the challenge widget has not been injected yet.
        """
        for shadow_root in await self.find_shadow_roots(deep=False):
            with contextlib.suppress(Exception):
                if _CLOUDFLARE_CHALLENGE_DOMAIN in await shadow_root.inner_html:
                    return shadow_root
        return None

    @staticmethod
    async def _click_cloudflare_checkbox(shadow_root: ShadowRoot) -> None:
        """Traverse the Turnstile widget and click its verification checkbox.

        Navigates shadow root -> challenge iframe -> body -> inner shadow root
        and clicks the ``input[type="checkbox"]`` element. Every step fails
        fast (``timeout=0``): any node captured here can go stale while
        Cloudflare re-renders the iframe, and polling locally on a stale node
        both wastes time and can let four sequential waits overrun the caller's
        deadline. Failing fast lets ``_bypass_cloudflare`` restart the whole
        traversal from the top on its next poll.
        """
        iframe = await shadow_root.query(_CLOUDFLARE_IFRAME_SELECTOR, timeout=0)
        body = await iframe.find(tag_name='body', timeout=0)
        inner_shadow = await body.get_shadow_root(timeout=0)
        checkbox = await inner_shadow.query(_CLOUDFLARE_CHECKBOX_SELECTOR, timeout=0)
        await checkbox.click()



    async def find_shadow_roots(self, deep: bool = False, timeout: float = 0) -> list[ShadowRoot]:
        """
        Find all shadow roots in the page.

        Traverses the entire DOM tree (including iframes and nested shadow DOMs)
        to collect all shadow roots found. This is especially useful when the
        shadow host element selector is unknown or dynamic (e.g., Cloudflare
        challenge pages).

        Args:
            deep: If True, also traverses cross-origin iframes (OOPIFs) to
                discover shadow roots inside them. The returned ShadowRoot
                objects will automatically route CDP commands through the
                correct OOPIF session.
            timeout: Maximum seconds to wait for shadow roots to appear.
                When > 0, repeatedly polls the DOM (every 0.5s) until at least
                one shadow root is found or the timeout expires. Useful when
                shadow hosts are injected asynchronously (e.g., Cloudflare
                Turnstile loading inside an OOPIF).

        Returns:
            List of ShadowRoot instances found in the page.

        Raises:
            WaitElementTimeout: If timeout > 0 and no shadow roots are found
                within the specified duration.
        """
        logger.debug('Finding all shadow roots in page (timeout=%s)', timeout)

        if not timeout:
            return await self._collect_all_shadow_roots(deep)

        start_time = asyncio.get_event_loop().time()
        while True:
            shadow_roots = await self._collect_all_shadow_roots(deep)
            if shadow_roots:
                return shadow_roots

            if asyncio.get_event_loop().time() - start_time > timeout:
                raise WaitElementTimeout(
                    f'Timed out after {timeout}s waiting for shadow roots in page'
                )

            await asyncio.sleep(0.5)


    async def _collect_all_shadow_roots(self, deep: bool) -> list[ShadowRoot]:
        """Collect shadow roots from the main document and optionally OOPIFs."""
        response: GetDocumentResponse = await self._execute_command(
            DomCommands.get_document(depth=-1, pierce=True)
        )
        root_node = response.get('result', {}).get('root', {})

        shadow_root_entries: list[tuple[Node, int | None]] = []
        self._collect_shadow_roots_from_tree(root_node, shadow_root_entries)

        shadow_roots: list[ShadowRoot] = []
        for shadow_data, host_backend_id in shadow_root_entries:
            backend_node_id = shadow_data.get('backendNodeId')
            if not backend_node_id:
                continue

            try:
                resolve_response: ResolveNodeResponse = await self._execute_command(
                    DomCommands.resolve_node(backend_node_id=backend_node_id)
                )
                shadow_object_id = resolve_response['result']['object']['objectId']
            except (CommandExecutionTimeout, WebSocketConnectionClosed, KeyError):
                logger.debug(f'Failed to resolve shadow root: backend_node_id={backend_node_id}')
                continue

            try:
                host_element = await self._resolve_shadow_host(host_backend_id)
            except (CommandExecutionTimeout, WebSocketConnectionClosed, KeyError):
                logger.debug(f'Failed to resolve shadow host: backend_node_id={host_backend_id}')
                host_element = None
            mode = ShadowRootType(shadow_data.get('shadowRootType', 'open'))
            shadow_roots.append(
                ShadowRoot(
                    object_id=shadow_object_id,
                    connection_handler=self._connection_handler,
                    mode=mode,
                    host_element=host_element,
                )
            )

        if deep:
            oopif_roots = await self._collect_oopif_shadow_roots()
            shadow_roots.extend(oopif_roots)

        logger.debug(f'Found {len(shadow_roots)} shadow roots')
        return shadow_roots

    @staticmethod
    def _collect_shadow_roots_from_tree(node: Node, results: list[tuple[Node, int | None]]) -> None:
        """Recursively walk a DOM tree collecting shadow root entries."""
        host_backend_id = node.get('backendNodeId')
        for shadow_root in node.get('shadowRoots', []):
            results.append((shadow_root, host_backend_id))
            _ts._collect_shadow_roots_from_tree(shadow_root, results)

        for child in node.get('children', []):
            _ts._collect_shadow_roots_from_tree(child, results)

        content_doc = node.get('contentDocument')
        if content_doc:
            _ts._collect_shadow_roots_from_tree(content_doc, results)


    async def _resolve_shadow_host(self, host_backend_id: int | None) -> WebElement | None:
        """Resolve the host element for a shadow root (best-effort)."""
        if not host_backend_id:
            return None

        host_response: ResolveNodeResponse = await self._execute_command(
            DomCommands.resolve_node(backend_node_id=host_backend_id)
        )
        host_object_id = host_response['result']['object']['objectId']
        host_attrs = await self._get_object_attributes(object_id=host_object_id)
        return WebElement(
            host_object_id, self._connection_handler, attributes_list=host_attrs, mouse=self._mouse
        )
    
    
    async def _collect_oopif_shadow_roots(self) -> list[ShadowRoot]:
        """Discover shadow roots inside cross-origin iframes (OOPIFs)."""
        browser_handler = ConnectionHandler(connection_port=self._connection_port)
        targets_response: GetTargetsResponse = await browser_handler.execute_command(
            TargetCommands.get_targets()
        )

        target_infos = targets_response.get('result', {}).get('targetInfos', [])
        iframe_targets = [t for t in target_infos if t.get('type') == 'iframe']

        if not iframe_targets:
            logger.debug('No OOPIF targets found')
            return []

        shadow_roots: list[ShadowRoot] = []
        for target in iframe_targets:
            roots = await self._collect_shadow_roots_from_oopif_target(target, browser_handler)
            shadow_roots.extend(roots)

        logger.debug(f'Found {len(shadow_roots)} shadow roots in OOPIFs')
        return shadow_roots
    
    async def _collect_shadow_roots_from_oopif_target(
        self,
        target: TargetInfo,
        browser_handler: ConnectionHandler,
    ) -> list[ShadowRoot]:
        """Collect shadow roots from a single OOPIF target."""
        target_id = target.get('targetId', '')
        try:
            attach_response: AttachToTargetResponse = await browser_handler.execute_command(
                TargetCommands.attach_to_target(target_id=target_id, flatten=True)
            )
            session_id = attach_response.get('result', {}).get('sessionId')
            if not session_id:
                return []
        except (CommandExecutionTimeout, WebSocketConnectionClosed):
            logger.debug(f'Failed to attach to OOPIF target: {target_id}')
            return []

        try:
            get_doc_command = DomCommands.get_document(depth=-1, pierce=True)
            get_doc_command['sessionId'] = session_id
            doc_response: GetDocumentResponse = await browser_handler.execute_command(
                get_doc_command
            )
            root_node = doc_response.get('result', {}).get('root', {})
        except (CommandExecutionTimeout, WebSocketConnectionClosed):
            logger.debug(f'Failed to get document from OOPIF target: {target_id}')
            return []

        entries: list[tuple[Node, int | None]] = []
        self._collect_shadow_roots_from_tree(root_node, entries)

        iframe_context = IFrameContext(
            frame_id=target_id,
            session_handler=browser_handler,
            session_id=session_id,
        )

        results: list[ShadowRoot] = []
        for shadow_data, host_backend_id in entries:
            sr = await self._resolve_oopif_shadow_entry(
                shadow_data, host_backend_id, browser_handler, session_id, iframe_context
            )
            if sr:
                results.append(sr)
        return results
    
    async def _resolve_oopif_shadow_entry(
        self,
        shadow_data: Node,
        host_backend_id: int | None,
        browser_handler: ConnectionHandler,
        session_id: str,
        iframe_context: IFrameContext,
    ) -> ShadowRoot | None:
        """Resolve a single shadow root entry from an OOPIF."""
        backend_node_id = shadow_data.get('backendNodeId')
        if not backend_node_id:
            return None

        try:
            resolve_command = DomCommands.resolve_node(backend_node_id=backend_node_id)
            resolve_command['sessionId'] = session_id
            resolve_response: ResolveNodeResponse = await browser_handler.execute_command(
                resolve_command
            )
            shadow_object_id = resolve_response['result']['object']['objectId']
        except (CommandExecutionTimeout, WebSocketConnectionClosed, KeyError):
            logger.debug(f'Failed to resolve OOPIF shadow root: backend_node_id={backend_node_id}')
            return None

        host_element = await self._resolve_oopif_shadow_host(
            host_backend_id, browser_handler, session_id
        )

        if host_element:
            host_element._iframe_context = iframe_context

        mode = ShadowRootType(shadow_data.get('shadowRootType', 'open'))
        sr = ShadowRoot(
            object_id=shadow_object_id,
            connection_handler=self._connection_handler,
            mode=mode,
            host_element=host_element,
        )

        if not host_element:
            sr._iframe_context = iframe_context

        return sr
    
    
    
    async def _resolve_oopif_shadow_host(
        self,
        host_backend_id: int | None,
        browser_handler: ConnectionHandler,
        session_id: str,
    ) -> WebElement | None:
        """Resolve the host element for a shadow root inside an OOPIF (best-effort)."""
        if not host_backend_id:
            return None

        try:
            resolve_command = DomCommands.resolve_node(backend_node_id=host_backend_id)
            resolve_command['sessionId'] = session_id
            host_response: ResolveNodeResponse = await browser_handler.execute_command(
                resolve_command
            )
            host_object_id = host_response['result']['object']['objectId']

            describe_command = DomCommands.describe_node(object_id=host_object_id)
            describe_command['sessionId'] = session_id
            describe_response: DescribeNodeResponse = await browser_handler.execute_command(
                describe_command
            )
            node_info = describe_response.get('result', {}).get('node', {})
            attributes = node_info.get('attributes', [])
            tag_name = node_info.get('nodeName', '').lower()
            attributes.extend(['tag_name', tag_name])

            return WebElement(
                host_object_id,
                self._connection_handler,
                attributes_list=attributes,
                mouse=self._mouse,
            )
        except (CommandExecutionTimeout, WebSocketConnectionClosed, KeyError):
            logger.debug(f'Failed to resolve OOPIF shadow host: backend_node_id={host_backend_id}')
            return None
    
    
    
    
