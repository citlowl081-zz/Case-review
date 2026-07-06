"""LangChain LCEL chain — the core RAG pipeline with streaming support."""
import json
from typing import AsyncIterator, List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from app.core.config import settings
from app.rag.prompts import QA_SYSTEM_PROMPT, REVIEW_PROMPTS, REVIEW_TYPE_LABELS
from app.rag.retriever import get_hybrid_retriever
from app.rag.reranker import get_reranker


def get_llm(streaming: bool = True) -> ChatOpenAI:
    """Get DashScope-compatible ChatOpenAI instance (阿里云百炼)."""
    return ChatOpenAI(
        model=settings.LLM_MODEL_NAME,
        api_key=settings.DASHSCOPE_API_KEY,
        base_url=settings.DASHSCOPE_BASE_URL,
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_TOKENS,
        streaming=streaming,
    )


def _build_context(docs_with_scores: List[tuple]) -> str:
    """Build formatted context string from retrieved documents with citation markers."""
    parts = []
    for i, (doc, score) in enumerate(docs_with_scores, 1):
        source = doc.metadata.get("source", "未知文档")
        page = doc.metadata.get("page", None)
        page_info = f", 第{page + 1}页" if page is not None else ""
        parts.append(f"[{i}] 来源: {source}{page_info} (相关度: {score:.2f})\n{doc.page_content}")
    return "\n\n".join(parts)


def _extract_citations(docs_with_scores: List[tuple]) -> List[Dict[str, Any]]:
    """Extract citation metadata from retrieved documents."""
    citations = []
    for i, (doc, score) in enumerate(docs_with_scores, 1):
        citations.append({
            "index": i,
            "doc_name": doc.metadata.get("source", "未知文档"),
            "chunk_text": doc.page_content[:300],
            "page": doc.metadata.get("page"),
            "chunk_id": doc.metadata.get("chunk_id"),
            "score": round(score, 3),
        })
    return citations


async def rag_qa_stream(
    query: str,
    chat_history: List[Dict[str, str]] = None,
) -> AsyncIterator[Dict[str, Any]]:
    """RAG Q&A with streaming output.

    Args:
        query: User's question
        chat_history: Previous messages in this session

    Yields:
        Dict with 'type': 'token' | 'citations' | 'done' | 'error'
    """
    try:
        # 1. Retrieve relevant documents
        retriever = get_hybrid_retriever()
        retrieved = retriever.retrieve(query)

        if not retrieved:
            yield {"type": "token", "content": "根据当前知识库中的文档，未找到相关信息。请上传相关临床试验文档后再提问。"}
            yield {"type": "done"}
            return

        # 2. Re-rank
        reranker = get_reranker()
        reranked = reranker.rerank(query, retrieved)

        # 3. Build context and prompt
        context = _build_context(reranked)
        citations = _extract_citations(reranked)

        # Send citations first so frontend can prepare
        yield {"type": "citations", "citations": citations}

        # 4. Build messages
        messages = [
            SystemMessage(content=QA_SYSTEM_PROMPT.format(context=context, question=query)),
        ]

        # Add recent chat history for context
        if chat_history:
            for msg in chat_history[-10:]:  # Last 10 messages
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                else:
                    from langchain_core.messages import AIMessage
                    messages.append(AIMessage(content=msg["content"]))

        messages.append(HumanMessage(content=query))

        # 5. Stream LLM response
        llm = get_llm(streaming=True)
        full_response = ""

        async for chunk in llm.astream(messages):
            if chunk.content:
                full_response += chunk.content
                yield {"type": "token", "content": chunk.content}

        yield {"type": "done", "full_response": full_response}

    except Exception as e:
        yield {"type": "error", "message": f"问答处理出错: {str(e)}"}


async def run_clinical_review(
    content: str,
    review_type: str,
    context_docs: List[Document] = None,
) -> Dict[str, Any]:
    """Run a clinical trial review agent.

    Args:
        content: The content to review (case record, lab report, etc.)
        review_type: One of 'visit_window', 'inclusion_exclusion', 'ae_logic', 'consistency'
        context_docs: Relevant reference documents from the knowledge base

    Returns:
        Review result dict with findings
    """
    prompt_template = REVIEW_PROMPTS.get(review_type)
    if not prompt_template:
        return {"error": f"未知审核类型: {review_type}", "findings": []}

    # Retrieve relevant context if not provided
    if context_docs is None:
        retriever = get_hybrid_retriever()
        retrieved = retriever.retrieve(content, top_k=5)
        context = _build_context(retrieved) if retrieved else "暂无参考文档"
    else:
        dummy = [(d, 1.0) for d in context_docs]
        context = _build_context(dummy)

    prompt = prompt_template.format(context=context, content=content)

    llm = get_llm(streaming=False)
    response = llm.invoke([HumanMessage(content=prompt)])

    return {
        "review_type": review_type,
        "review_type_label": REVIEW_TYPE_LABELS.get(review_type, review_type),
        "content": response.content,
        "raw_findings": response.content,
    }
