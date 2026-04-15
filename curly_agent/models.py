from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class CandidateItem:
    source_section: str
    title: str
    url: str
    image_url: str
    position: int
    description: str = ""
    published_at: str = ""
    price_text: str = ""
    item_id: str = ""
    is_new: bool = False
    detail_text: str = ""
    detail_images: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    content_type: str = ""
    highlights: list[str] = field(default_factory=list)
    uncertainties: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SelectionResult:
    item: CandidateItem
    reason: str
