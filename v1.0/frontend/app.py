import requests
import streamlit as st
from datetime import datetime

# BACKEND_URL = "http://127.0.0.1:8000"
BACKEND_URL = "http://127.0.0.1:58000"

st.set_page_config(
    page_title="私有知识库问答",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("私有知识库问答系统")
st.caption("支持知识库问答、文档上传、文档删除与来源追溯")

# -----------------------------
# 工具函数
# -----------------------------
def init_state():
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "doc_refresh_nonce" not in st.session_state:
        st.session_state.doc_refresh_nonce = 0


def safe_request(method, url, **kwargs):
    try:
        resp = requests.request(method, url, timeout=kwargs.pop("timeout", 60), **kwargs)
        return resp, None
    except requests.exceptions.ConnectionError:
        return None, "无法连接后端服务，请确认后端是否启动。"
    except requests.exceptions.Timeout:
        return None, "请求超时，请稍后重试。"
    except Exception as e:
        return None, f"请求异常：{str(e)}"


def ask_question(question, top_k):
    resp, err = safe_request(
        "POST",
        f"{BACKEND_URL}/ask",
        json={"question": question, "top_k": top_k},
        timeout=180,
    )
    if err:
        return None, err

    if resp.status_code != 200:
        return None, f"后端返回错误：{resp.text}"

    try:
        return resp.json(), None
    except Exception:
        return None, "后端返回的数据不是合法 JSON。"


def get_documents():
    # 用 nonce 触发 rerun 后刷新
    _ = st.session_state.doc_refresh_nonce

    resp, err = safe_request(
        "GET",
        f"{BACKEND_URL}/documents",
        timeout=60,
    )
    if err:
        return None, err

    if resp.status_code != 200:
        return None, resp.text

    try:
        return resp.json(), None
    except Exception:
        return None, "文档列表返回格式错误。"


def upload_document(uploaded_file):
    files = {
        "file": (
            uploaded_file.name,
            uploaded_file.getvalue(),
            uploaded_file.type or "application/octet-stream"
        )
    }
    resp, err = safe_request(
        "POST",
        f"{BACKEND_URL}/upload",
        files=files,
        timeout=300,
    )
    if err:
        return None, err

    if resp.status_code != 200:
        return None, resp.text

    try:
        return resp.json(), None
    except Exception:
        return None, "上传成功，但返回数据格式异常。"


def delete_document(doc_id):
    resp, err = safe_request(
        "DELETE",
        f"{BACKEND_URL}/documents/{doc_id}",
        timeout=120,
    )
    if err:
        return False, err

    if resp.status_code != 200:
        return False, resp.text

    return True, None


def format_time(time_str):
    if not time_str:
        return "-"
    try:
        return time_str[:19].replace("T", " ")
    except Exception:
        return str(time_str)


def add_chat_record(question, answer, sources):
    st.session_state.chat_history.append({
        "question": question,
        "answer": answer,
        "sources": sources or [],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })


def clear_chat_history():
    st.session_state.chat_history = []


def render_source_list(sources):
    if not sources:
        st.info("没有返回参考来源")
        return

    for idx, item in enumerate(sources, start=1):
        file_name = item.get("file_name", "未知文件")
        chunk_index = item.get("chunk_index", "-")
        preview = item.get("preview", "")

        with st.expander(f"{idx}. {file_name} ｜ chunk={chunk_index}", expanded=False):
            st.code(preview or "无预览内容", language="text")


def render_latest_answer():
    if not st.session_state.chat_history:
        st.info("还没有提问记录，先输入一个问题试试。")
        return

    latest = st.session_state.chat_history[-1]

    st.subheader("最新回答")
    st.markdown(f"**问题：** {latest['question']}")
    st.caption(f"时间：{latest.get('created_at', '-')}")
    st.markdown("**回答：**")
    st.write(latest["answer"])

    # st.markdown("**参考来源：**")
    # render_source_list(latest["sources"])
    with st.expander(f"参考来源（{len(latest['sources'])}）", expanded=False):
        render_source_list(latest["sources"])


def render_history():
    history = st.session_state.chat_history
    if len(history) <= 1:
        return

    st.markdown("---")
    st.subheader("历史记录")

    old_history = list(reversed(history[:-1]))
    for i, chat in enumerate(old_history, start=1):
        title = f"{chat.get('created_at', '')} ｜ {chat['question'][:40]}..."
        with st.expander(title, expanded=False):
            st.markdown(f"**问题：** {chat['question']}")
            st.markdown("**回答：**")
            st.write(chat["answer"])
            st.markdown("**参考来源：**")
            render_source_list(chat["sources"])


# -----------------------------
# 初始化
# -----------------------------
init_state()

tab1, tab2 = st.tabs(["问答", "文档管理"])

# -----------------------------
# Tab 1: 问答
# -----------------------------
with tab1:
    left, right = st.columns([3, 1])

    with left:
        render_latest_answer()

    with right:
        st.subheader("操作")
        st.metric("累计提问", len(st.session_state.chat_history))
        if st.button("清空历史记录", use_container_width=True):
            clear_chat_history()
            st.rerun()

        st.markdown("### 示例问题")
        example_questions = [
            "报销流程是什么？",
            "年假申请怎么走？",
            "试用期考核标准是什么？",
            "出差审批需要哪些材料？"
        ]
        for q in example_questions:
            if st.button(q, key=f"example_{q}", use_container_width=True):
                st.session_state.question_input = q

    st.markdown("---")

    st.subheader("发起提问")
    with st.form("ask_form", clear_on_submit=False):
        question = st.text_area(
            "请输入你的问题",
            height=120,
            placeholder="例如：报销流程是什么？",
            key="question_input"
        )
        top_k = st.slider("返回参考片段数量", 1, 50, 5)

        submitted = st.form_submit_button("开始提问", use_container_width=True)

    if submitted:
        if not question.strip():
            st.warning("请输入问题")
        else:
            with st.spinner("正在检索并生成答案..."):
                data, err = ask_question(question.strip(), top_k)

            if err:
                st.error(err)
            else:
                add_chat_record(
                    question=question.strip(),
                    answer=data.get("answer", ""),
                    sources=data.get("sources", [])
                )
                # st.session_state.question_input = ""
                st.rerun()

    render_history()


# -----------------------------
# Tab 2: 文档管理
# -----------------------------
with tab2:
    st.subheader("上传文档")
    st.caption("支持 pdf / txt / md / docx")

    uploaded = st.file_uploader(
        "选择文件",
        type=["pdf", "txt", "md", "docx"],
        help="上传后将进入知识库，可用于后续问答。"
    )

    upload_col1, upload_col2 = st.columns([3, 1])

    with upload_col1:
        if st.button("上传并入库", use_container_width=True):
            if not uploaded:
                st.warning("请先选择文件")
            else:
                with st.spinner("正在上传并入库..."):
                    result, err = upload_document(uploaded)

                if err:
                    st.error(err)
                else:
                    st.success(f"上传成功：{uploaded.name}")
                    st.json(result)
                    st.session_state.doc_refresh_nonce += 1
                    st.rerun()

    with upload_col2:
        if st.button("刷新文档列表", use_container_width=True):
            st.session_state.doc_refresh_nonce += 1
            st.rerun()

    st.markdown("---")
    st.subheader("文档列表")

    docs, err = get_documents()

    if err:
        st.error(err)
    else:
        if not docs:
            st.info("当前没有文档")
        else:
            total_docs = len(docs)
            total_chunks = sum(doc.get("chunks", 0) for doc in docs if isinstance(doc.get("chunks", 0), int))

            m1, m2 = st.columns(2)
            m1.metric("文档数量", total_docs)
            m2.metric("总分片数", total_chunks)

            st.markdown("### 已入库文档")

            header = st.columns([4, 2, 2, 1])
            header[0].markdown("**文件名**")
            header[1].markdown("**Chunks**")
            header[2].markdown("**上传时间**")
            header[3].markdown("**操作**")

            for doc in docs:
                doc_id = doc.get("doc_id")
                file_name = doc.get("file_name", "-")
                chunks = doc.get("chunks", "-")
                uploaded_at = format_time(doc.get("uploaded_at"))

                cols = st.columns([4, 2, 2, 1])
                cols[0].write(file_name)
                cols[1].write(str(chunks))
                cols[2].write(uploaded_at)

                if cols[3].button("删除", key=f"delete_{doc_id}"):
                    with st.spinner(f"正在删除 {file_name}..."):
                        ok, delete_err = delete_document(doc_id)

                    if ok:
                        st.success(f"已删除：{file_name}")
                        st.session_state.doc_refresh_nonce += 1
                        st.rerun()
                    else:
                        st.error(delete_err)