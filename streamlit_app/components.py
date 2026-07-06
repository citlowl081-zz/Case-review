"""Shared UI components for the Streamlit app."""
import streamlit as st
from core.models import DOC_TYPE_LABELS


def render_doc_type_select(label="文档类型", key="doc_type"):
    """Render a document type selector."""
    options = [(k, f"{v} ({k})") for k, v in DOC_TYPE_LABELS.items()]
    return st.selectbox(
        label,
        options=[k for k, _ in options],
        format_func=lambda x: DOC_TYPE_LABELS.get(x, x),
        key=key,
    )


def render_doc_subtype_input(doc_type: str, key="doc_subtype"):
    """Render subtype input based on doc type."""
    if doc_type == "visit_record":
        return st.text_input("访视阶段", placeholder="如 V1, V2, V3", key=key)
    return ""


def render_severity_badge(severity: str) -> str:
    """Return emoji for severity level."""
    return {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(severity, "⚪")


def render_finding_type_badge(finding_type: str) -> str:
    """Return label for finding type."""
    return {
        "definite": "明确问题",
        "suspected": "疑似问题",
        "suggestion": "建议确认",
    }.get(finding_type, finding_type)


def format_finding_card(finding: dict) -> None:
    """Render a single finding as an expandable card."""
    severity = finding.get("severity", "medium")
    ftype = finding.get("type", "suspected")
    badge = render_severity_badge(severity)
    type_label = render_finding_type_badge(ftype)

    with st.expander(
        f"{badge} [{type_label}] {finding.get('title', '无标题')[:80]}",
        expanded=(severity == "high"),
    ):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**风险等级**: {badge} {severity}")
            st.markdown(f"**审核类型**: {finding.get('review_category', '')}")
        with col2:
            st.markdown(f"**涉及文件**: {finding.get('source_files', '')}")

        st.markdown("**问题描述**")
        st.text(finding.get("description", ""))

        if finding.get("evidence"):
            st.markdown("**判断依据**")
            st.info(finding["evidence"])

        if finding.get("suggestion"):
            st.markdown("**建议处理方式**")
            st.warning(finding["suggestion"])

        if finding.get("risk_impact"):
            st.markdown("**风险影响**")
            st.error(finding["risk_impact"])

        if finding.get("query_statement"):
            st.markdown("**建议澄清语句**")
            query_text = finding["query_statement"]
            st.code(query_text, language=None)
            # Use a hidden text area for copy functionality
            copy_key = f"copy_{hash(query_text)}_{finding.get('title', '')[:10]}"
            st.text_area(
                "📋 复制上方语句",
                value=query_text,
                key=copy_key,
                height=60,
                label_visibility="collapsed",
            )
            st.caption("👆 选中文本后 Cmd+C 复制")


def render_status_badge(status: str) -> str:
    """Return colored status indicator."""
    mapping = {
        "running": "🔄 审核中",
        "completed": "✅ 已完成",
        "failed": "❌ 失败",
        "active": "🟢 进行中",
        "archived": "📦 已归档",
    }
    return mapping.get(status, status)
