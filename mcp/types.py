from dataclasses import dataclass

from typing import Any, Dict


@dataclass
class TextContent:
    type: str
    text: str


@dataclass
class JsonContent:
    type: str
    data: Dict[str, Any]
