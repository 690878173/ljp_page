from enum import Enum

from typing_extensions import TypedDict

from ..base import Command, EmptyParams, EmptyResponse, Response
from .types import AXNode, AXNodeId


class AccessibilityMethod(str, Enum):
    """可访问性域方法名称。"""

    DISABLE = 'Accessibility.disable'
    ENABLE = 'Accessibility.enable'
    GET_PARTIAL_AX_TREE = 'Accessibility.getPartialAXTree'
    GET_FULL_AX_TREE = 'Accessibility.getFullAXTree'
    GET_ROOT_AX_NODE = 'Accessibility.getRootAXNode'
    GET_AX_NODE_AND_ANCESTORS = 'Accessibility.getAXNodeAndAncestors'
    GET_CHILD_AX_NODES = 'Accessibility.getChildAXNodes'
    QUERY_AX_TREE = 'Accessibility.queryAXTree'


class GetPartialAXTreeParams(TypedDict, total=False):
    """getPartialAXTree 命令的参数。"""

    nodeId: int
    backendNodeId: int
    objectId: str
    fetchRelatives: bool


class GetFullAXTreeParams(TypedDict, total=False):
    """getFullAXTree 命令的参数。"""

    depth: int
    frameId: str


class GetRootAXNodeParams(TypedDict, total=False):
    """getRootAXNode 命令的参数。"""

    frameId: str


class GetAXNodeAndAncestorsParams(TypedDict, total=False):
    """getAXNodeAndAncestors 命令的参数。"""

    nodeId: int
    backendNodeId: int
    objectId: str


class GetChildAXNodesParams(TypedDict, total=False):
    """getChildAXNodes 命令的参数。"""

    id: AXNodeId
    frameId: str


class QueryAXTreeParams(TypedDict, total=False):
    """queryAXTree 命令的参数。"""

    nodeId: int
    backendNodeId: int
    objectId: str
    accessibleName: str
    role: str


#结果类型
class GetPartialAXTreeResult(TypedDict):
    """getPartialAXTree 命令的结果。"""

    nodes: list[AXNode]


class GetFullAXTreeResult(TypedDict):
    """getFullAXTree 命令的结果。"""

    nodes: list[AXNode]


class GetRootAXNodeResult(TypedDict):
    """getRootAXNode 命令的结果。"""

    node: AXNode


class GetAXNodeAndAncestorsResult(TypedDict):
    """getAXNodeAndAncestors 命令的结果。"""

    nodes: list[AXNode]


class GetChildAXNodesResult(TypedDict):
    """getChildAXNodes 命令的结果。"""

    nodes: list[AXNode]


class QueryAXTreeResult(TypedDict):
    """queryAXTree 命令的结果。"""

    nodes: list[AXNode]


#响应类型
GetPartialAXTreeResponse = Response[GetPartialAXTreeResult]
GetFullAXTreeResponse = Response[GetFullAXTreeResult]
GetRootAXNodeResponse = Response[GetRootAXNodeResult]
GetAXNodeAndAncestorsResponse = Response[GetAXNodeAndAncestorsResult]
GetChildAXNodesResponse = Response[GetChildAXNodesResult]
QueryAXTreeResponse = Response[QueryAXTreeResult]

#命令类型
DisableCommand = Command[EmptyParams, Response[EmptyResponse]]
EnableCommand = Command[EmptyParams, Response[EmptyResponse]]
GetPartialAXTreeCommand = Command[GetPartialAXTreeParams, GetPartialAXTreeResponse]
GetFullAXTreeCommand = Command[GetFullAXTreeParams, GetFullAXTreeResponse]
GetRootAXNodeCommand = Command[GetRootAXNodeParams, GetRootAXNodeResponse]
GetAXNodeAndAncestorsCommand = Command[GetAXNodeAndAncestorsParams, GetAXNodeAndAncestorsResponse]
GetChildAXNodesCommand = Command[GetChildAXNodesParams, GetChildAXNodesResponse]
QueryAXTreeCommand = Command[QueryAXTreeParams, QueryAXTreeResponse]
