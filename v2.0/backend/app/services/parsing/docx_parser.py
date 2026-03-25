import re
from typing import Any, Dict, List, Optional, Tuple

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

from app.services.parsing.base import BaseParser
from app.services.chunking.models import Block


def iter_block_items(doc):
    from docx.document import Document as _Document
    from docx.oxml.table import CT_Tbl
    from docx.oxml.text.paragraph import CT_P
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    parent_elm = doc.element.body if isinstance(doc, _Document) else doc._element
    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, doc)
        elif isinstance(child, CT_Tbl):
            yield Table(child, doc)


def table_to_markdown(table: Table) -> str:
    rows = []
    for row in table.rows:
        cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
        rows.append(cells)
    if not rows:
        return ""
    max_cols = max(len(r) for r in rows)
    rows = [r + [""] * (max_cols - len(r)) for r in rows]
    header = rows[0]
    sep = ["---"] * max_cols
    body = rows[1:]
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(sep) + " |"]
    for r in body:
        lines.append("| " + " | ".join(r) + " |")
    return "\n".join(lines)


class DocxParser(BaseParser):
    CHAPTER_PATTERNS = [
        re.compile(r"^\s*第[一二三四五六七八九十百千万0-9]+章[\s　]+.+$"),
        re.compile(r"^\s*第[一二三四五六七八九十百千万0-9]+编[\s　]+.+$"),
        re.compile(r"^\s*第[一二三四五六七八九十百千万0-9]+部分[\s　]+.+$"),
    ]
    ARTICLE_PATTERNS = [re.compile(r"^\s*第[一二三四五六七八九十百千万0-9]+条\b.*$")]
    SECTION_PATTERNS = [re.compile(r"^\s*[一二三四五六七八九十]+、.+$")]
    SUBSECTION_PATTERNS = [
        re.compile(r"^\s*（[一二三四五六七八九十]+）.+$"),
        re.compile(r"^\s*\([一二三四五六七八九十]+\).+$"),
    ]
    ITEM_PATTERNS = [
        re.compile(r"^\s*[0-9]+[\.、].+$"),
        re.compile(r"^\s*（[0-9]+）.+$"),
        re.compile(r"^\s*\([0-9]+\).+$"),
    ]
    APPENDIX_PATTERNS = [
        re.compile(r"^\s*附件[一二三四五六七八九十0-9]*[:：]?\s*.*$"),
        re.compile(r"^\s*附表[一二三四五六七八九十0-9]*[:：]?\s*.*$"),
    ]

    def parse(self, file_path) -> List[Block]:
        doc = Document(file_path)
        blocks: List[Block] = []
        hierarchy: List[Tuple[int, str]] = []
        current_block: Optional[Block] = None

        for item in iter_block_items(doc):
            if isinstance(item, Paragraph):
                text = self._normalize_text(item.text)
                if not text:
                    continue
                block_type, level = self._classify_paragraph(text)

                if block_type in {"chapter", "appendix"}:
                    current_block = self._flush_current(blocks, current_block)
                    hierarchy = self._update_hierarchy(hierarchy, level, text)
                    blocks.append(Block(type="heading", text=text, level=level, path=self._path_from_hierarchy(hierarchy), heading=text, metadata={"kind": block_type}))

                elif block_type in {"article", "section", "subsection", "item"}:
                    current_block = self._flush_current(blocks, current_block)
                    hierarchy = self._update_hierarchy(hierarchy, level, text)
                    current_block = Block(type="clause", text=text, level=level, path=self._path_from_hierarchy(hierarchy), heading=text, metadata={"kind": block_type})

                else:
                    if current_block is None:
                        current_block = Block(type="paragraph", text=text, level=(hierarchy[-1][0] + 1) if hierarchy else 0, path=self._path_from_hierarchy(hierarchy), heading=hierarchy[-1][1] if hierarchy else None, metadata={"kind": "paragraph"})
                    else:
                        current_block.text += "\n" + text

            elif isinstance(item, Table):
                table_text = table_to_markdown(item)
                if not table_text.strip():
                    continue
                current_block = self._flush_current(blocks, current_block)
                blocks.append(Block(type="table", text=table_text, level=(hierarchy[-1][0] + 1) if hierarchy else 0, path=self._path_from_hierarchy(hierarchy), heading=hierarchy[-1][1] if hierarchy else None, metadata={"kind": "table"}))

        current_block = self._flush_current(blocks, current_block)
        return blocks

    def _normalize_text(self, text: str) -> str:
        text = text.replace("\u3000", " ")
        return re.sub(r"[ \t]+", " ", text).strip()

    def _classify_paragraph(self, text: str) -> Tuple[str, int]:
        if self._match_any(text, self.CHAPTER_PATTERNS): return "chapter", 1
        if self._match_any(text, self.APPENDIX_PATTERNS): return "appendix", 1
        if self._match_any(text, self.ARTICLE_PATTERNS): return "article", 2
        if self._match_any(text, self.SECTION_PATTERNS): return "section", 3
        if self._match_any(text, self.SUBSECTION_PATTERNS): return "subsection", 4
        if self._match_any(text, self.ITEM_PATTERNS): return "item", 5
        return "paragraph", 99

    def _match_any(self, text: str, patterns: List[re.Pattern]) -> bool:
        return any(p.match(text) for p in patterns)

    def _update_hierarchy(self, hierarchy, level, title):
        while hierarchy and hierarchy[-1][0] >= level:
            hierarchy.pop()
        hierarchy.append((level, title))
        return hierarchy

    def _path_from_hierarchy(self, hierarchy):
        return [title for _, title in hierarchy]

    def _flush_current(self, blocks, current_block):
        if current_block and current_block.text.strip():
            blocks.append(current_block)
        return None
