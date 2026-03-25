from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Block:
    type: str
    text: str
    level: int = 0
    path: List[str] = field(default_factory=list)
    heading: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Chunk:
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
