from venv import logger
from app.services.llm import chat_llm
import re

REWRITE_SYSTEM_PROMPT = """
你是企业知识库检索的查询改写器。

任务：
把用户问题改写成更适合知识库检索的单条查询语句。

严格要求：
1. 只输出最终查询语句
2. 不要提问
3. 不要解释
4. 不要输出前缀，如“改写后：”“查询：”
5. 不要输出序号、引号、项目符号
6. 信息不足时也要尽量基于原问题改写
7. 输出只能是一行中文文本
"""


def _clean_rewrite(text: str, fallback: str) -> str:
    if not text:
        return fallback

    text = text.strip().replace("\n", " ")

    # 去掉常见前缀
    text = re.sub(r"^(改写后[:：]\s*|查询[:：]\s*|检索语句[:：]\s*|输出[:：]\s*)", "", text)
    text = re.sub(r'^[\"\“\”\']+|[\"\“\”\']+$', "", text)
    text = re.sub(r"^\d+[\.、]\s*", "", text)

    # 如果明显不是检索语句，而是在对话
    bad_patterns = [
        "请提供",
        "请补充",
        "更多信息",
        "具体背景",
        "以便我",
        "需要更多上下文",
        "无法为您",
        "才能为您",
    ]
    if any(p in text for p in bad_patterns):
        return fallback

    return text or fallback


def rewrite_query(question: str) -> str:
    question = (question or "").strip()
    if not question:
        return ""

    try:
        resp = chat_llm.invoke(
            [
                ("system", REWRITE_SYSTEM_PROMPT),
                ("user", f"用户问题：{question}"),
            ]
        )
        content = resp.content if isinstance(resp.content, str) else str(resp.content)
        rewritten = _clean_rewrite(content, question)

        logger.info("Query original: %s", question)
        logger.info("Query rewritten: %s", rewritten)
        return rewritten

    except Exception:
        return question