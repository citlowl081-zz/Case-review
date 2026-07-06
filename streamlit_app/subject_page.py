"""Subject management page — create subjects and upload their documents."""
import streamlit as st
from core.database import (
    get_project, get_project_subjects, create_subject, delete_subject, get_subject,
    get_project_documents,
)
from core.models import DOC_TYPE_LABELS


def render_subject_page():
    """Render subject management page."""
    project_id = st.session_state.get("selected_project_id")
    if not project_id:
        st.warning("请先选择一个项目")
        return

    project = get_project(project_id)
    if not project:
        st.error("项目不存在")
        return

    st.title(f"👤 受试者管理 — {project.name}")

    # Check if project has protocol documents
    project_docs = get_project_documents(project_id, subject_id=None)
    completed_docs = [d for d in project_docs if d.parse_status == "completed"]
    if not completed_docs:
        st.warning("⚠️ 项目还没有已完成处理的项目文件（方案/手册等）。请先在「项目管理」页面上传方案文档，否则审核将缺少依据。")

    st.markdown("---")

    # ── Create Subject ──
    with st.expander("➕ 创建受试者", expanded=len(get_project_subjects(project_id)) == 0):
        col1, col2 = st.columns(2)
        with col1:
            code = st.text_input("受试者编号 *", placeholder="如 S-001-042", key="new_subj_code")
        with col2:
            initials = st.text_input("姓名缩写", placeholder="如 WXM", key="new_subj_initials")
        if st.button("创建受试者", type="primary") and code.strip():
            s = create_subject(project_id, code.strip(), initials.strip())
            st.success(f"受试者 {s.subject_code} 创建成功！")
            st.session_state.selected_subject_id = s.id
            st.rerun()

    # ── Subject List ──
    st.subheader("受试者列表")
    subjects = get_project_subjects(project_id)
    if not subjects:
        st.info("暂无受试者，请先创建")
        return

    for s in subjects:
        selected = st.session_state.get("selected_subject_id") == s.id
        bg = "#e6f4ff" if selected else None

        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            with col1:
                st.markdown(f"**{s.subject_code}**")
                if s.initials:
                    st.caption(f"缩写: {s.initials}")
            with col2:
                st.caption(f"状态: {s.status}")
            with col3:
                subj_docs = get_project_documents(project_id, subject_id=s.id)
                st.caption(f"文件: {len(subj_docs)} 个")
            with col4:
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("📂", key=f"opnsubj_{s.id}", help="选择此受试者"):
                        st.session_state.selected_subject_id = s.id
                        st.rerun()
                with c2:
                    if st.button("🗑️", key=f"delsubj_{s.id}", help="删除"):
                        delete_subject(s.id)
                        if st.session_state.get("selected_subject_id") == s.id:
                            st.session_state.selected_subject_id = None
                        st.rerun()

    # ── Selected Subject Detail ──
    selected_id = st.session_state.get("selected_subject_id")
    if selected_id:
        st.markdown("---")
        _render_subject_detail(selected_id)


def _render_subject_detail(subject_id: str):
    """Render subject detail with document upload."""
    subject = get_subject(subject_id)
    if not subject:
        return

    st.subheader(f"📋 受试者: {subject.subject_code}")

    tab1, tab2 = st.tabs(["📄 已有文件", "📤 上传文件"])

    with tab1:
        docs = get_project_documents(subject.project_id, subject_id=subject_id)
        if not docs:
            st.info("暂无受试者文件")
        else:
            for doc in docs:
                dtype_label = DOC_TYPE_LABELS.get(doc.doc_type, doc.doc_type)
                status_emoji = {"pending": "⏳", "completed": "✅", "failed": "❌"}.get(doc.parse_status, "❓")
                with st.container(border=True):
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.markdown(f"**{doc.original_filename}**")
                        st.caption(f"{dtype_label} | {status_emoji} {doc.parse_status}")
                    with c2:
                        if st.button("🗑️", key=f"delsubjdoc_{doc.id}"):
                            from core.database import delete_document
                            import os
                            try:
                                from rag.engine import delete_document_chunks
                                delete_document_chunks(subject.project_id, doc.id)
                            except Exception:
                                pass
                            if doc.file_path and os.path.exists(doc.file_path):
                                os.remove(doc.file_path)
                            delete_document(doc.id)
                            st.rerun()

    with tab2:
        _render_subject_upload(subject)


def _render_subject_upload(subject):
    """Render upload form for subject documents."""
    uploaded_file = st.file_uploader(
        "选择受试者文件",
        type=["pdf", "docx", "doc", "xlsx", "xls", "txt", "md", "csv"],
        key=f"subj_uploader_{subject.id}",
    )

    col1, col2 = st.columns(2)
    with col1:
        doc_type = st.selectbox(
            "文档类型",
            options=[
                "screening_record", "baseline_record", "visit_record",
                "lab_report", "diary_card", "prick_test",
                "ae_record", "cm_record", "drug_dispense", "other",
            ],
            format_func=lambda x: DOC_TYPE_LABELS.get(x, x),
            key=f"subj_doc_type_{subject.id}",
        )
    with col2:
        if doc_type == "visit_record":
            st.text_input("访视阶段", placeholder="如 V1, V2, V3", key=f"subj_doc_subtype_{subject.id}")

    if uploaded_file and st.button("⬆️ 上传受试者文件", key=f"subj_upload_btn_{subject.id}", type="primary"):
        from streamlit_app.project_page import _process_upload
        with st.spinner("正在处理文件..."):
            _process_upload(uploaded_file, subject.project_id, subject.id, doc_type)
        st.rerun()
