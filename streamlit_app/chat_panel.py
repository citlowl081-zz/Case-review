"""Global Q&A panel — always-visible right-side chat with RAG retrieval."""
import streamlit as st
import json
import sys
import os

_backend_dir = os.path.join(os.path.dirname(__file__), '..', 'backend')
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from langchain_core.messages import HumanMessage, SystemMessage
from app.rag.chain import get_llm
from core.database import add_chat_message, get_chat_messages
from rag.engine import search_all_projects

QA_SYSTEM_PROMPT = """你是一个临床试验知识助手。你基于知识库中的文档内容回答用户的问题。

## 回答规则
1. **严格依据文档**：所有回答必须基于知识库检索到的文档内容，不得臆测
2. **引用来源**：每个结论注明来自哪个文档
3. **诚实面对不确定性**：如果文档中找不到答案，明确告知
4. **专业术语**：使用临床试验领域规范术语
5. **简洁清晰**：直接回答问题，不要过度展开
"""


def render_chat_panel():
    """Render the always-visible right-side Q&A panel."""
    # ── Init session state ──
    if "qa_collapsed" not in st.session_state:
        st.session_state.qa_collapsed = False

    # ── Header with collapse toggle ──
    col1, col2 = st.columns([4, 1])
    with col1:
        st.subheader("💬 知识问答")
    with col2:
        if st.button("🔽" if not st.session_state.qa_collapsed else "◀", key="qa_toggle",
                     help="折叠/展开问答面板"):
            st.session_state.qa_collapsed = not st.session_state.qa_collapsed
            st.rerun()

    if st.session_state.qa_collapsed:
        st.caption("点击 ◀ 展开问答面板")
        return

    st.caption("基于所有已上传文档的 RAG 智能问答")
    st.divider()

    # ── Load history from DB ──
    project_id = st.session_state.get("selected_project_id")
    db_messages = get_chat_messages(project_id)

    # ── Display chat messages ──
    chat_container = st.container(height=400)
    with chat_container:
        if not db_messages:
            st.info(
                "👋 欢迎使用知识问答！\n\n"
                "你可以问我任何临床试验相关的问题，我会从已上传的方案、手册、"
                "研究者手册等文档中检索答案。\n\n"
                "例如：\n"
                "- 什么是访视窗口？\n"
                "- 不良事件的严重程度如何分级？\n"
                "- 试验药物的保存条件是什么？"
            )

        for msg in db_messages:
            with st.chat_message(msg.role):
                st.markdown(msg.content)
                if msg.citations and msg.citations != "[]":
                    try:
                        cites = json.loads(msg.citations)
                        if cites:
                            with st.expander("📎 引用来源"):
                                for c in cites:
                                    st.caption(f"• {c}")
                    except (json.JSONDecodeError, TypeError):
                        pass

    # ── Input area ──
    question = None
    if st.session_state.get("page") == "review" and st.session_state.get("active_report_id"):
        st.caption("💡 审核追问请在中间区域输入")
    else:
        st.divider()
        question = st.chat_input("基于知识库提问...", key="qa_chat_input")

    if question:
        project_id = st.session_state.get("selected_project_id")

        # Save + display user message
        add_chat_message(project_id, "user", question)

        with chat_container:
            with st.chat_message("user"):
                st.markdown(question)

        # Generate answer
        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner("🔍 正在检索知识库..."):
                    answer, citations = _rag_answer(question, db_messages[-6:] if db_messages else [])

        # Save + display assistant message
        citations_json = json.dumps(citations, ensure_ascii=False)
        add_chat_message(project_id, "assistant", answer, citations_json)

        st.rerun()


def _rag_answer(question: str, chat_history: list) -> tuple:
    """Generate an answer using RAG retrieval + LLM.

    Returns: (answer_text, citations_list)
    """
    # 1. RAG search across all projects
    docs = search_all_projects(question, top_k=5)

    # 2. Build context
    citations = []
    context_parts = []

    if docs:
        for i, (doc, score) in enumerate(docs, 1):
            src = doc.metadata.get("filename", doc.metadata.get("source", "未知文档"))
            project_name = doc.metadata.get("project_name", "")
            label = f"{src}"
            if project_name:
                label = f"{project_name} / {src}"

            context_parts.append(f"[{i}] {label} (相关度: {score:.2f})\n{doc.page_content[:600]}")
            citations.append(f"[{i}] {label}")

        context = "\n\n---\n".join(context_parts)
    else:
        context = "（知识库中暂无相关文档，请先上传方案或手册等文件）"

    # 3. Build history context
    history_text = ""
    if chat_history:
        parts = []
        for msg in chat_history[-6:]:
            role = "用户" if msg.role == "user" else "助手"
            parts.append(f"{role}: {msg.content[:300]}")
        history_text = "\n".join(parts)

    # 4. Call LLM
    prompt = f"""## 知识库检索结果
{context}

## 对话历史
{history_text or "（新对话）"}

## 用户问题
{question}

请基于知识库检索结果回答问题。"""

    try:
        llm = get_llm(streaming=False)
        response = llm.invoke([
            SystemMessage(content=QA_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])
        return response.content, citations
    except Exception as e:
        return f"抱歉，回答失败: {str(e)}\n\n请确认：\n1. 是否已上传文档到知识库？\n2. API Key 是否有效？", citations
