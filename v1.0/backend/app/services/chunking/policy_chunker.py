import re
from typing import List, Dict, Any, Optional

from app.services.chunking.models import Block, Chunk


def policy_chunk(blocks: List[Block], max_chars: int = 1000) -> List[Chunk]:
    chunks: List[Chunk] = []

    # 当前章节级标题栈，只维护 heading，不包含 clause
    heading_stack: List[str] = []

    # 当前条款缓冲
    current_clause_parts: List[str] = []
    current_clause_meta: Optional[Dict[str, Any]] = None

    # 没有 clause 时的散落正文缓冲
    loose_parts: List[str] = []
    loose_meta: Optional[Dict[str, Any]] = None

    def build_prefix(headings: List[str]) -> str:
        """
        chunk 正文前缀只放章节级标题，避免 clause 标题重复出现在正文里
        """
        return "\n".join(headings).strip()

    def split_text_smart(text: str, limit: int) -> List[str]:
        """
        超长文本的制度类智能切分：
        1. 优先按句号/分号/问号/感叹号/换行切
        2. 单句过长时再硬切
        """
        text = text.strip()
        if not text:
            return []

        if len(text) <= limit:
            return [text]

        pieces = re.split(r"(?<=[。；！？\n])", text)
        result: List[str] = []
        current = ""

        for piece in pieces:
            piece = piece.strip()
            if not piece:
                continue

            # 单段本身过长，硬切
            if len(piece) > limit:
                if current:
                    result.append(current.strip())
                    current = ""

                for i in range(0, len(piece), limit):
                    sub = piece[i:i + limit].strip()
                    if sub:
                        result.append(sub)
                continue

            candidate = f"{current}{piece}"
            if len(candidate) <= limit:
                current = candidate
            else:
                if current:
                    result.append(current.strip())
                current = piece

        if current:
            result.append(current.strip())

        return result

    def emit_chunk(
        body: str,
        *,
        strategy: str,
        headings: List[str],
        block_type: str,
        path: Optional[List[str]] = None,
        source_block: Optional[Block] = None,
        chunk_index: Optional[int] = None,
        chunk_total: Optional[int] = None,
    ):
        body = body.strip()
        if not body:
            return

        prefix = build_prefix(headings)
        final_text = f"{prefix}\n{body}".strip() if prefix else body

        metadata: Dict[str, Any] = {
            "strategy": strategy,
            "headings": headings.copy(),
            "title_path": " > ".join(headings),
            "block_type": block_type,
            "path": (path or []).copy(),
        }

        if source_block is not None:
            metadata.update(
                {
                    "block_level": source_block.level,
                    "block_heading": source_block.heading,
                    "block_kind": source_block.metadata.get("kind"),
                }
            )

        if chunk_index is not None and chunk_total is not None:
            metadata.update(
                {
                    "chunk_index": chunk_index,
                    "chunk_total": chunk_total,
                }
            )

        chunks.append(Chunk(text=final_text, metadata=metadata))

    def flush_loose():
        nonlocal loose_parts, loose_meta

        if not loose_parts:
            return

        body = "\n".join(loose_parts).strip()
        if body and loose_meta:
            prefix = build_prefix(loose_meta["headings"])
            reserved = len(prefix) + 1 if prefix else 0
            body_limit = max(200, max_chars - reserved)

            parts = split_text_smart(body, body_limit)
            total = len(parts)

            for idx, part in enumerate(parts, start=1):
                emit_chunk(
                    part,
                    strategy=loose_meta["strategy"],
                    headings=loose_meta["headings"],
                    block_type=loose_meta["block_type"],
                    path=loose_meta.get("path"),
                    source_block=loose_meta.get("source_block"),
                    chunk_index=idx if total > 1 else None,
                    chunk_total=total if total > 1 else None,
                )

        loose_parts = []
        loose_meta = None

    def flush_clause():
        nonlocal current_clause_parts, current_clause_meta

        if not current_clause_parts:
            return

        if not current_clause_meta:
            current_clause_parts = []
            return

        full_body = "\n".join(current_clause_parts).strip()
        if not full_body:
            current_clause_parts = []
            current_clause_meta = None
            return

        headings = current_clause_meta["headings"]
        source_block = current_clause_meta.get("source_block")
        path = current_clause_meta.get("path")

        prefix = build_prefix(headings)
        reserved = len(prefix) + 1 if prefix else 0
        body_limit = max(200, max_chars - reserved)

        parts = split_text_smart(full_body, body_limit)
        total = len(parts)

        for idx, part in enumerate(parts, start=1):
            emit_chunk(
                part,
                strategy="policy_clause",
                headings=headings,
                block_type="clause",
                path=path,
                source_block=source_block,
                chunk_index=idx if total > 1 else None,
                chunk_total=total if total > 1 else None,
            )

        current_clause_parts = []
        current_clause_meta = None

    def update_heading_stack(block: Block):
        nonlocal heading_stack

        level = block.level or 1

        if level <= len(heading_stack):
            heading_stack[:] = heading_stack[: level - 1]

        heading_stack.append(block.text)

    for block in blocks:
        text = (block.text or "").strip()
        if not text:
            continue

        if block.type == "heading":
            flush_loose()
            flush_clause()
            update_heading_stack(block)

        elif block.type == "clause":
            flush_loose()
            flush_clause()

            current_clause_parts = [text]
            current_clause_meta = {
                "headings": heading_stack.copy(),
                "path": block.path.copy(),
                "source_block": block,
            }

        elif block.type == "paragraph":
            if current_clause_meta is not None:
                # paragraph 归并到最近 clause
                current_clause_parts.append(text)
            else:
                # 没有 clause 时，作为散落正文处理
                if loose_meta is None:
                    loose_meta = {
                        "strategy": "policy_paragraph",
                        "headings": heading_stack.copy(),
                        "block_type": "paragraph",
                        "path": block.path.copy(),
                        "source_block": block,
                    }
                loose_parts.append(text)

        elif block.type == "table":
            flush_loose()
            flush_clause()

            emit_chunk(
                text,
                strategy="policy_table",
                headings=heading_stack.copy(),
                block_type="table",
                path=block.path.copy(),
                source_block=block,
            )

        else:
            # 未知类型兜底，当作普通正文处理
            if current_clause_meta is not None:
                current_clause_parts.append(text)
            else:
                if loose_meta is None:
                    loose_meta = {
                        "strategy": "policy_other",
                        "headings": heading_stack.copy(),
                        "block_type": block.type,
                        "path": block.path.copy(),
                        "source_block": block,
                    }
                loose_parts.append(text)

    flush_loose()
    flush_clause()
    return chunks