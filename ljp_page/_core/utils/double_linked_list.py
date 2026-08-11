from __future__ import annotations
from typing import Generic, TypeVar, Optional

T = TypeVar("T")


class ListNode(Generic[T]):
    __slots__ = ("data", "prev", "next")

    def __init__(self, data: T):
        self.data: T = data
        self.prev: Optional[ListNode[T]] = None
        self.next: Optional[ListNode[T]] = None


class DoubleLinkedList(Generic[T]):
    """通用双向链表，带虚拟头、尾哨兵，简化边界判断"""
    def __init__(self):
        # 哨兵节点，不存业务数据
        self._head = ListNode(None)
        self._tail = ListNode(None)
        self._head.next = self._tail
        self._tail.prev = self._head
        self._size = 0

    @property
    def size(self) -> int:
        return self._size

    def push_front(self, node: ListNode[T]) -> None:
        """把节点插入链表头部（最近使用）"""
        # 先解绑旧位置
        self._detach(node)
        nxt = self._head.next
        node.prev = self._head
        node.next = nxt
        self._head.next = node
        if nxt:
            nxt.prev = node
        self._size += 1

    def pop_back(self) -> Optional[ListNode[T]]:
        """弹出链表尾部节点（最久未使用），返回节点；空返回None"""
        if self._size == 0:
            return None
        node = self._tail.prev
        self._detach(node)
        return node

    def remove(self, node: ListNode[T]) -> None:
        """删除指定节点，O(1)"""
        self._detach(node)

    def _detach(self, node: ListNode[T]) -> None:
        """把节点从链表剥离，不销毁节点本身"""
        prev_node = node.prev
        next_node = node.next
        if prev_node is not None:
            prev_node.next = next_node
        if next_node is not None:
            next_node.prev = prev_node
        node.prev = None
        node.next = None
        if self._size > 0:
            self._size -= 1

    def clear(self) -> None:
        """清空链表"""
        self._head.next = self._tail
        self._tail.prev = self._head
        self._size = 0

    def __iter__(self):
        """遍历，调试用"""
        cur = self._head.next
        while cur is not None and cur is not self._tail:
            yield cur.data
            cur = cur.next



__all__ = ['DoubleLinkedList',"ListNode"]