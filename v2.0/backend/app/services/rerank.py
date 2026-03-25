import re
from typing import List
import logging
from langchain_core.documents import Document
from app.services.llm import chat_llm

logger = logging.getLogger(__name__)

RERANK_PROMPT = """
你是一个信息检索排序模型。

任务：
根据"问题"，判断哪些文本片段最有助于回答问题，并按相关性排序。

规则：
1. 只看"是否能直接回答问题"
2. 优先选择包含明确结论/规则/数字/条件的内容
3. 忽略泛泛介绍
4. 输出最相关的前 {top_k} 个编号

问题：
{question}

候选文本：
{candidates}

请只输出一个数组，例如：
[3,1,5]
"""


def rerank_with_llm(question: str, docs: List[Document], top_k: int = 5) -> List[Document]:
    if not docs:
        return []
    candidates_text = [f"{i}. {d.page_content[:500].replace(chr(10), ' ')}" for i, d in enumerate(docs, 1)]
    prompt = RERANK_PROMPT.format(question=question, candidates="\n".join(candidates_text), top_k=top_k)
    try:
        resp = chat_llm.invoke([("system", "你是一个排序助手"), ("user", prompt)])
        content = resp.content if isinstance(resp.content, str) else str(resp.content)
        nums = re.findall(r"\d+", content)
        indices = [int(n) - 1 for n in nums]
        reranked = [docs[i] for i in indices if 0 <= i < len(docs)]
        return reranked[:top_k] if reranked else docs[:top_k]
    except Exception:
        return docs[:top_k]
