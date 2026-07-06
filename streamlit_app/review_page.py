"""Review page — chat-first interface: review report + RAG-powered follow-up Q&A."""
import streamlit as st
import json
import sys
import os
from datetime import datetime

# Ensure backend accessible
_backend_dir = os.path.join(os.path.dirname(__file__), '..', 'backend')
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from langchain_core.messages import HumanMessage, SystemMessage
from app.rag.chain import get_llm

from core.database import (
    get_project, get_subject, get_project_documents,
    create_report, save_report, fail_report,
    get_subject_reports, get_report, get_report_findings,
    add_findings, add_timeline_events, add_kb_issue,
    get_report_conversations, add_conversation,
)
from agents.orchestrator import Orchestrator
from reports.builder import ReportBuilder
from rag.engine import search as rag_search


# ── Follow-up Q&A Prompt ──

FOLLOWUP_SYSTEM_PROMPT = """你是一个临床试验质控专家助手。用户正在审核一份病历的质控报告，并对审核结果进行追问。

## 回答规则
1. 优先引用审核报告中的发现（如果报告中有相关内容）
2. 补充引用方案原文条款（从知识库检索到的内容）
3. 如果审核报告和方案都没有覆盖用户的问题，如实告知
4. 每个结论注明来源：是来自"审核报告"还是"方案原文"
5. 简洁专业，不要过度展开

## 引用格式
在回答中使用 [报告] 表示引用审核报告，[方案] 表示引用方案原文。
"""


# ═══════════════════════════════════════════════════════════════
#  Main Page Renderer
# ═══════════════════════════════════════════════════════════════

def render_review_page():
    """Render the chat-first review page."""
    project_id = st.session_state.get("selected_project_id")
    subject_id = st.session_state.get("selected_subject_id")

    if not project_id or not subject_id:
        st.warning("请先在侧边栏选择项目和受试者")
        return

    project = get_project(project_id)
    subject = get_subject(subject_id)
    if not project or not subject:
        st.error("项目或受试者不存在")
        return

    # ── Sidebar: Controls ──
    _render_sidebar(project, subject)

    # ── Main Area: Chat ──
    _render_chat_area(project, subject)


# ═══════════════════════════════════════════════════════════════
#  Sidebar
# ═══════════════════════════════════════════════════════════════

def _render_sidebar(project, subject):
    """Inline control bar for review actions."""
    with st.container():
        st.subheader(f"📁 {project.name}")
        st.caption(f"👤 {subject.subject_code}")

        # Document counts
        proto_docs = get_project_documents(project.id, subject_id=None)
        subj_docs = get_project_documents(project.id, subject_id=subject.id)
        completed_proto = [d for d in proto_docs if d.parse_status == "completed"]
        completed_subj = [d for d in subj_docs if d.parse_status == "completed"]

        col1, col2 = st.columns(2)
        with col1:
            st.metric("方案文件", len(completed_proto))
        with col2:
            st.metric("受试者文件", len(completed_subj))

        st.divider()

        # Start Review button
        can_review = len(completed_proto) > 0 and len(completed_subj) > 0
        if st.button(
            "🚀 开始自动审核",
            type="primary",
            use_container_width=True,
            disabled=not can_review,
            key="start_review_btn",
        ):
            if can_review:
                st.session_state.pending_review = True
                st.rerun()

        if not can_review:
            if not completed_proto:
                st.caption("⚠️ 请先上传方案文档")
            if not completed_subj:
                st.caption("⚠️ 请先上传受试者文件")

        st.divider()

        # Historical reports
        st.caption("── 历史审核报告 ──")
        reports = get_subject_reports(subject.id)
        if reports:
            for r in reports:
                label = _report_label(r)
                selected = st.session_state.get("active_report_id") == r.id
                btn_type = "primary" if selected else "secondary"
                if st.button(
                    label,
                    key=f"report_{r.id}",
                    use_container_width=True,
                    type=btn_type,
                ):
                    st.session_state.active_report_id = r.id
                    st.rerun()
        else:
            st.caption("暂无审核报告")


def _report_label(report) -> str:
    """Generate a compact label for a report."""
    status_icon = {"completed": "✅", "running": "🔄", "failed": "❌"}.get(report.status, "❓")
    conclusion_icon = {
        "no_issue": "🟢",
        "needs_confirm": "🟡",
        "has_issue": "🔴",
        "critical": "🚨",
    }.get(report.overall_conclusion, "❓")
    date_str = report.created_at[:16] if report.created_at else ""
    return f"{status_icon} {conclusion_icon} {date_str}"


# ═══════════════════════════════════════════════════════════════
#  Chat Area
# ═══════════════════════════════════════════════════════════════

def _render_chat_area(project, subject):
    """Render the chat interface with review report and follow-up Q&A."""
    active_report_id = st.session_state.get("active_report_id")
    active_report = get_report(active_report_id) if active_report_id else None

    # Title
    if active_report:
        st.caption(
            f"审核报告 {active_report_id[:8]}... | "
            f"{active_report.created_at[:16] if active_report.created_at else ''}"
        )
    else:
        st.info("👈 点击侧边栏「开始审核」或选择一个历史报告")

    # ── Display conversation ──
    conversations = []
    if active_report_id:
        conversations = get_report_conversations(active_report_id)

    # Render report summary at top (only if report exists and isn't already saved as first message)
    first_is_report = (
        conversations
        and conversations[0].role == "assistant"
        and "审核完成" in (conversations[0].content or "")
    )

    if active_report and active_report.status == "completed" and not first_is_report:
        _render_report_as_message(active_report, active_report_id)

    # Render conversations
    for i, conv in enumerate(conversations):
        with st.chat_message(conv.role):
            st.markdown(conv.content)

            # For the report message (first one), show full report expander
            if i == 0 and first_is_report and active_report and active_report.report_markdown:
                with st.expander("📋 查看完整12章节审核报告", expanded=False):
                    st.markdown(active_report.report_markdown)

            # Show citations for Q&A messages
            if conv.citations and conv.citations != "[]":
                try:
                    cites = json.loads(conv.citations)
                    if cites:
                        with st.expander("📎 引用来源"):
                            for c in cites:
                                st.caption(f"• {c}")
                except (json.JSONDecodeError, TypeError):
                    pass

    # ── Pending review execution ──
    if st.session_state.get("pending_review"):
        st.session_state.pending_review = False
        with st.spinner("🔄 正在执行自动审核（9个Agent并行运行中，预计30-90秒）..."):
            _execute_review(project, subject)
        st.rerun()

    # ── Chat input ──
    if active_report_id and active_report and active_report.status == "completed":
        question = st.chat_input(
            "输入追问，如：点刺试验有没有问题？方案中访视窗口是多少天？AE有没有漏记？"
        )
        if question:
            # Save user message
            add_conversation(active_report_id, "user", question)

            # Show immediately
            with st.chat_message("user"):
                st.markdown(question)

            # Generate answer
            with st.chat_message("assistant"):
                with st.spinner("检索中..."):
                    answer, citations = _answer_followup(
                        project_id=project.id,
                        report_id=active_report_id,
                        question=question,
                        chat_history=conversations[-10:],  # Last 10 turns
                    )
                    st.markdown(answer)
                    if citations:
                        with st.expander("📎 引用来源"):
                            for c in citations:
                                st.caption(f"• {c}")

            # Save assistant response
            add_conversation(
                active_report_id, "assistant", answer,
                citations=json.dumps(citations, ensure_ascii=False),
            )
            st.rerun()


# ═══════════════════════════════════════════════════════════════
#  Review Execution
# ═══════════════════════════════════════════════════════════════

def _execute_review(project, subject):
    """Run the full review pipeline and save results."""
    proto_docs = [d for d in get_project_documents(project.id, subject_id=None) if d.parse_status == "completed"]
    subj_docs = [d for d in get_project_documents(project.id, subject_id=subject.id) if d.parse_status == "completed"]

    try:
        report = create_report(project.id, subject.id)
        report_id = report.id

        # Prepare context
        protocol_context = "\n\n".join([
            f"=== {d.original_filename} ===\n{d.extracted_text or ''}"
            for d in proto_docs
        ])
        subject_data = "\n\n".join([
            f"=== {d.original_filename} (类型: {d.doc_type}) ===\n{d.extracted_text or ''}"
            for d in subj_docs
        ])

        # Run orchestrator
        orch = Orchestrator(max_workers=3)
        result = orch.run_review(
            project_id=project.id,
            protocol_context=protocol_context,
            subject_data=subject_data,
        )

        # Build and save report
        builder = ReportBuilder(project.name, subject.subject_code)
        markdown = builder.build(result, subj_docs, proto_docs)
        report_json = json.dumps(result.get("agent_results", {}), ensure_ascii=False, default=str)

        save_report(
            report_id=report_id,
            markdown=markdown,
            report_json=report_json,
            conclusion=result.get("conclusion", "unknown"),
            risk_summary=result.get("risk_summary", ""),
        )

        # Save findings
        all_findings = result.get("all_findings", [])
        if all_findings:
            add_findings(report_id, all_findings)
            for f in all_findings[:20]:
                if f.get("title"):
                    add_kb_issue(
                        category=f.get("review_category", "other"),
                        title=f.get("title", ""),
                        description=f.get("description", ""),
                        typical_query=f.get("query_statement", ""),
                    )

        # Save timeline
        timeline = result.get("timeline_events", [])
        if timeline:
            add_timeline_events(report_id, timeline)

        # Save to file backup
        from core.utils import get_report_dir
        report_dir = get_report_dir(project.id)
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / f"{subject.subject_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(markdown)

        # Save report summary as first conversation message
        conclusion_emoji = {
            "no_issue": "✅ 无明显问题",
            "needs_confirm": "⚠️ 存在需确认问题",
            "has_issue": "❌ 存在明确问题",
            "critical": "🚨 可能影响入组或数据质量",
        }.get(result.get("conclusion", ""), "❓")
        stats = result.get("stats", {})
        report_msg = (
            f"## 🏥 审核完成\n\n"
            f"**总体结论: {conclusion_emoji}**\n\n"
            f"{result.get('risk_summary', '')}\n\n"
            f"| 指标 | 数量 |\n|------|------|\n"
            f"| 发现总数 | {stats.get('total_findings', 0)} |\n"
            f"| 明确问题 | {stats.get('definite', 0)} |\n"
            f"| 疑似问题 | {stats.get('suspected', 0)} |\n"
            f"| 高风险 | {stats.get('high_severity', 0)} |\n"
            f"| 中风险 | {stats.get('medium_severity', 0)} |\n\n"
            f"💡 你可以在下方输入框追问任何审核相关的问题。"
        )
        add_conversation(report_id, "assistant", report_msg)

        st.session_state.active_report_id = report_id

    except Exception as e:
        fail_report(report_id, str(e))
        import traceback
        st.error(f"审核失败: {str(e)}")
        if os.getenv("DEBUG", "false").lower() == "true":
            st.code(traceback.format_exc())


# ═══════════════════════════════════════════════════════════════
#  Follow-up Q&A
# ═══════════════════════════════════════════════════════════════

def _answer_followup(
    project_id: str,
    report_id: str,
    question: str,
    chat_history: list = None,
):
    """Answer a follow-up question using RAG + review findings.

    Returns: (answer_text, citations_list)
    """
    # 1. Get relevant findings from the review report
    findings = get_report_findings(report_id)
    relevant_findings = _match_findings(question, findings)

    # 2. RAG search in project knowledge base
    rag_context = ""
    citations = []
    try:
        rag_docs = rag_search(project_id, question, top_k=5)
        if rag_docs:
            rag_parts = []
            for i, (doc, score) in enumerate(rag_docs, 1):
                src = doc.metadata.get("filename", doc.metadata.get("source", "方案文档"))
                rag_parts.append(f"[方案{i}] {src}\n{doc.page_content[:500]}")
                citations.append(f"[方案{i}] {src}")
            rag_context = "\n\n".join(rag_parts)
    except Exception as e:
        rag_context = f"（RAG检索失败: {str(e)}）"

    # 3. Build context
    findings_context = ""
    if relevant_findings:
        findings_parts = []
        for i, f in enumerate(relevant_findings[:10], 1):
            findings_parts.append(
                f"[发现{i}] [{f.review_category}] {f.title or ''}\n"
                f"描述: {f.description or ''}\n"
                f"依据: {f.evidence or ''}\n"
                f"建议: {f.suggestion or ''}"
            )
        findings_context = "\n\n".join(findings_parts)
        for i, f in enumerate(relevant_findings[:10], 1):
            citations.append(f"[发现{i}] 审核报告 - {f.title or f.review_category}")

    # 4. Build chat history context
    history_context = ""
    if chat_history:
        history_parts = []
        for msg in chat_history[-6:]:
            role = "用户" if msg.role == "user" else "助手"
            history_parts.append(f"{role}: {msg.content[:300]}")
        history_context = "\n".join(history_parts)

    # 5. Call LLM
    prompt = f"""## 审核报告中的相关发现
{findings_context or "（审核报告中未找到与此问题直接相关的发现）"}

## 方案知识库检索结果
{rag_context or "（未检索到相关方案条款）"}

## 对话历史
{history_context or "（新对话）"}

## 用户问题
{question}

请基于以上信息回答用户的问题。如果审核报告中有相关发现，优先引用；补充方案原文条款作为依据。"""

    try:
        llm = get_llm(streaming=False)
        response = llm.invoke([
            SystemMessage(content=FOLLOWUP_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])
        return response.content, citations
    except Exception as e:
        return f"抱歉，回答失败: {str(e)}", []


def _match_findings(question: str, findings: list) -> list:
    """Simple keyword matching to find relevant findings."""
    if not findings:
        return []

    # Keywords mapping: question terms -> finding categories
    kw_map = {
        "点刺": ["prick_test"],
        "过敏": ["prick_test"],
        "皮试": ["prick_test"],
        "入排": ["inclusion"],
        "入选": ["inclusion"],
        "排除": ["inclusion"],
        "纳入": ["inclusion"],
        "时间": ["timeline"],
        "窗口": ["timeline"],
        "访视": ["timeline"],
        "超窗": ["timeline"],
        "顺序": ["timeline"],
        "日期": ["timeline"],
        "AE": ["ae"],
        "不良事件": ["ae"],
        "ae": ["ae"],
        "合并用药": ["cm"],
        "CM": ["cm"],
        "cm": ["cm"],
        "禁用": ["cm"],
        "用药": ["cm"],
        "检查": ["lab"],
        "化验": ["lab"],
        "实验室": ["lab"],
        "异常值": ["lab"],
        "药物": ["drug"],
        "依从": ["drug"],
        "服药": ["drug"],
        "发药": ["drug"],
        "回收": ["drug"],
        "完整性": ["completeness"],
        "漏填": ["completeness"],
        "错别字": ["completeness"],
        "模板": ["completeness"],
        "书写": ["completeness"],
        "澄清": ["query"],
        "Query": ["query"],
        "query": ["query"],
    }

    q_lower = question.lower()

    # Find matching categories
    matched_categories = set()
    for kw, cats in kw_map.items():
        if kw.lower() in q_lower:
            matched_categories.update(cats)

    if not matched_categories:
        # If no keyword match, return all findings (up to 15)
        return findings[:15]

    # Filter findings by matched categories
    relevant = []
    for f in findings:
        cat = getattr(f, 'review_category', '') or ''
        if cat in matched_categories:
            relevant.append(f)

    # Also include high-severity findings regardless of category
    for f in findings:
        sev = getattr(f, 'severity', '') or ''
        if sev == 'high' and f not in relevant:
            relevant.append(f)

    return relevant[:15]


# ═══════════════════════════════════════════════════════════════
#  Report as First Message
# ═══════════════════════════════════════════════════════════════

def _render_report_as_message(report, report_id):
    """Render the review report as the first assistant message in the chat."""
    conclusion_emoji = {
        "no_issue": "✅ 无明显问题",
        "needs_confirm": "⚠️ 存在需确认问题",
        "has_issue": "❌ 存在明确问题",
        "critical": "🚨 可能影响入组或数据质量",
    }.get(report.overall_conclusion, "❓")

    with st.chat_message("assistant"):
        st.markdown(f"## 🏥 审核报告\n\n**总体结论: {conclusion_emoji}**\n\n{report.overall_risk_summary or ''}")

        # Show stats
        findings = get_report_findings(report_id)
        if findings:
            definite = len([f for f in findings if f.finding_type == "definite"])
            suspected = len([f for f in findings if f.finding_type == "suspected"])
            high = len([f for f in findings if f.severity == "high"])
            cols = st.columns(4)
            cols[0].metric("总发现", len(findings))
            cols[1].metric("明确问题", definite)
            cols[2].metric("疑似问题", suspected)
            cols[3].metric("高风险", high)

        # Full report in expander
        if report.report_markdown:
            with st.expander("📋 查看完整12章节审核报告", expanded=False):
                st.markdown(report.report_markdown)

        st.caption("💡 你可以在下方输入框追问任何审核相关的问题，如：")
        st.caption("   • 这个受试者点刺试验有没有问题？")
        st.caption("   • AE记录有没有遗漏？时间逻辑有没有矛盾？")
        st.caption("   • 方案中关于访视窗口是怎么规定的？")
