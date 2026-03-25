import re
import logging
from typing import List
from app.services.chunking.models import Block

logger = logging.getLogger(__name__)


def classify_document(blocks: List[Block]) -> str:
    text = "\n".join(b.text for b in blocks[:50])
    heading_count = sum(1 for b in blocks if b.type == "heading")
    table_count = sum(1 for b in blocks if b.type == "table")

    policy_patterns = [r"第[一二三四五六七八九十]+条", r"第[一二三四五六七八九十]+章", r"\d+\.\d+", r"适用范围", r"审批流程", r"管理制度", r"员工手册"]
    faq_patterns = [r"问[:：]", r"答[:：]", r"Q[:：]", r"A[:：]"]

    if any(re.search(p, text) for p in faq_patterns):
        return "faq"
    if heading_count >= 5 and any(re.search(p, text) for p in policy_patterns):
        return "policy"
    if heading_count >= 3:
        return "structured"
    if table_count >= 10:
        return "table_heavy"
    return "generic"
