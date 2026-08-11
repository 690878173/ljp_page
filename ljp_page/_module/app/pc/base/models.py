"""流水线数据模型。"""

from typing import Any

from pydantic import BaseModel, Field, model_validator


# ---------- P1 ----------
class P1Item(BaseModel):
    """P1 列表项 —— 表示单个待抓取的条目（如一本小说）。"""

    name: str
    url: str
    description: str | None = None
    next_url: str | None = None
    other: Any = None


class P1Result(BaseModel):
    """P1 解析结果 —— 列表页的一次抓取产出。"""

    items: list[P1Item] = Field(default_factory=list)
    next_url: str | None = None

    def __len__(self) -> int:
        return len(self.items)

    def __bool__(self) -> bool:
        return bool(self.items)


# ---------- P2 ----------
class P3Item(BaseModel):
    """P3 内容项 —— 单个章节 / 剧集。"""

    url: str
    name: str
    p2_name: str = ""
    content: str = ""
    id: int | None = None
    description: str | None = None
    next_url: str | None = None
    other: Any = None


class P2Item(BaseModel):
    """P2 详情项 —— 单个抓取对象的详情（如小说信息 + 章节列表）。"""

    url: str
    name: str
    author: str
    description: str
    p3items: list[P3Item]
    next_url: str | None = None
    other: Any = None

    @model_validator(mode="after")
    def _assign_chapter_ids(self) -> "P2Item":
        p3_id = 1
        for p3 in self.p3items:
            if p3.id is None:
                p3.id = p3_id
            p3_id += 1
        return self

    @property
    def chapter_count(self) -> int:
        return len(self.p3items)


class P2Result(BaseModel):
    """P2 解析结果 —— 详情页的一次抓取产出。"""

    items: list[P2Item] = Field(default_factory=list)
    next_url: str | None = None
    other: Any = None

    def __len__(self) -> int:
        return len(self.items)

    def __bool__(self) -> bool:
        return bool(self.items)
