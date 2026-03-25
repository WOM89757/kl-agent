from typing import List
from venv import logger
from langchain_core.documents import Document
from app.services.llm import chat_llm


RERANK_PROMPT = """
你是一个信息检索排序模型。

任务：
根据“问题”，判断哪些文本片段最有助于回答问题，并按相关性排序。

规则：
1. 只看“是否能直接回答问题”
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


def rerank_with_llm(
    question: str,
    docs: List[Document],
    top_k: int = 5,
) -> List[Document]:
    if not docs:
        return []

    # 构造候选
    candidates_text = []
    for i, d in enumerate(docs, start=1):
        # text = d.page_content[:500].replace("\n", " ")
        text = d.page_content[:].replace("\n", " ")
        candidates_text.append(f"{i}. {text}")

    prompt = RERANK_PROMPT.format(
        question=question,
        candidates="\n".join(candidates_text),
        top_k=top_k,
    )

    try:
        resp = chat_llm.invoke(
            [
                ("system", "你是一个排序助手"),
                ("user", prompt),
            ]
        )

        content = resp.content if isinstance(resp.content, str) else str(resp.content)

        # 解析输出
        import re
        nums = re.findall(r"\d+", content)
        indices = [int(n) - 1 for n in nums]

        reranked = []
        for i in indices:
            if 0 <= i < len(docs):
                reranked.append(docs[i])

        # logger.info(f"Reranked results: {reranked}")
        # print("rerank检索到文档数量:", len(reranked))
        # for i, doc in enumerate(reranked):
        #     print(f"\n===== Doc {i} =====")
        #     print("内容:", doc.page_content[:200])
        #     print("元数据:", doc.metadata)
        
        return reranked[:top_k] if reranked else docs[:top_k]

    except Exception:
        # 出错 fallback
        return docs[:top_k]