"""Base parser interface."""
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class ParseResult:
    """Unified result from any document parser."""

    text: str = ""                          # Full extracted text
    tables: List[List[List[str]]] = field(default_factory=list)  # List of tables, each table is rows×cols
    tables_text: List[str] = field(default_factory=list)  # Tables rendered as text
    metadata: Dict[str, Any] = field(default_factory=dict)  # Extra metadata
    page_count: int = 0
    success: bool = False
    error: str = ""

    @property
    def full_text(self) -> str:
        """Return text + table text combined."""
        parts = [self.text]
        if self.tables_text:
            parts.append("\n\n--- 表格内容 ---\n")
            for i, t in enumerate(self.tables_text):
                parts.append(f"\n[表 {i+1}]\n{t}")
        return "\n".join(parts)


class BaseParser:
    """Base class for document parsers."""

    name: str = "base"
    formats: List[str] = []

    def parse(self, file_path: str) -> ParseResult:
        raise NotImplementedError
