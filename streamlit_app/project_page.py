"""Project detail page — upload protocol/IB/drug manual documents."""
import streamlit as st
import os
from core.database import (
    get_project, get_project_documents, create_document, delete_document,
    update_document_text,
)
from core.models import DOC_TYPE_LABELS
from core.utils import save_uploaded_file, get_file_format, ensure_project_dirs, get_project_dir
from parsers import parse_document
from rag.engine import load_and_index_document


def render_project_page():
    """Render the project detail page."""
    project_id = st.session_state.get("selected_project_id")
    if not project_id:
        st.warning("请先在首页选择一个项目")
        if st.button("← 返回首页"):
            st.session_state.page = "home"
            st.rerun()
        return

    project = get_project(project_id)
    if not project:
        st.error("项目不存在")
        return

    st.title(f"📁 {project.name}")
    if project.protocol_number:
        st.caption(f"方案编号: {project.protocol_number}")

    st.markdown("---")

    # ── Tabs ──
    tab1, tab2 = st.tabs(["📄 项目文件", "📤 上传文件"])

    with tab1:
        _render_document_list(project_id)

    with tab2:
        _render_upload_area(project_id)


def _render_document_list(project_id: str):
    """Render list of project-level documents."""
    docs = get_project_documents(project_id, subject_id=None)
    if not docs:
        st.info("暂无项目文件，请先上传研究方案、研究者手册或药物管理手册")
        return

    for doc in docs:
        dtype_label = DOC_TYPE_LABELS.get(doc.doc_type, doc.doc_type)
        status_emoji = {
            "pending": "⏳",
            "parsing": "🔄",
            "completed": "✅",
            "failed": "❌",
        }.get(doc.parse_status, "❓")

        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
            with col1:
                st.markdown(f"**{doc.original_filename}**")
                st.caption(f"类型: {dtype_label} | 格式: {doc.file_format}")
            with col2:
                st.caption(f"{status_emoji} {doc.parse_status}")
                if doc.chunk_count:
                    st.caption(f"向量块: {doc.chunk_count}")
            with col3:
                st.caption(f"{doc.file_size or 0:,} B" if doc.file_size else "")
            with col4:
                if st.button("🗑️", key=f"delprojdoc_{doc.id}"):
                    # Remove from ChromaDB
                    try:
                        from rag.engine import delete_document_chunks
                        delete_document_chunks(project_id, doc.id)
                    except Exception:
                        pass
                    # Remove file
                    if doc.file_path and os.path.exists(doc.file_path):
                        os.remove(doc.file_path)
                    delete_document(doc.id)
                    st.rerun()


def _render_upload_area(project_id: str):
    """Render upload form for project documents."""
    st.subheader("上传项目文件")
    st.caption("支持以下类型: 研究方案、研究者手册、药物管理手册")

    # Determine which doc types are project-level (not subject-level)
    project_doc_types = ["protocol", "investigator_brochure", "drug_manual", "other"]

    uploaded_file = st.file_uploader(
        "选择文件",
        type=["pdf", "docx", "doc", "xlsx", "xls", "txt", "md"],
        key="project_uploader",
        accept_multiple_files=False,
    )

    col1, col2 = st.columns(2)
    with col1:
        doc_type = st.selectbox(
            "文档类型",
            options=project_doc_types,
            format_func=lambda x: DOC_TYPE_LABELS.get(x, x),
        )
    with col2:
        st.caption("研究方案、研究者手册、药物管理手册等")

    if uploaded_file and st.button("⬆️ 上传", type="primary"):
        with st.spinner("正在处理文件..."):
            _process_upload(uploaded_file, project_id, None, doc_type)
        st.rerun()


def _process_upload(uploaded_file, project_id: str, subject_id: str, doc_type: str):
    """Process an uploaded file: save, parse, chunk, embed."""
    try:
        # Determine directories
        project = get_project(project_id)
        ensure_project_dirs(project_id)

        if subject_id:
            from core.database import get_subject
            subject = get_subject(subject_id)
            from core.utils import ensure_subject_dirs
            ensure_subject_dirs(project_id, subject.subject_code)
            from core.utils import get_subject_dir
            dest_dir = get_subject_dir(project_id, subject.subject_code) / "other"
        else:
            dest_dir = get_project_dir(project_id) / "raw" / doc_type

        # Save file
        saved_name, file_path, file_size = save_uploaded_file(
            uploaded_file, dest_dir, uploaded_file.name
        )

        file_format = get_file_format(uploaded_file.name)

        # Create DB record
        doc = create_document(
            project_id=project_id,
            subject_id=subject_id,
            doc_type=doc_type,
            filename=saved_name,
            original_filename=uploaded_file.name,
            file_path=file_path,
            file_size=file_size,
            file_format=file_format,
        )

        # Parse document
        result = parse_document(file_path, file_format)

        if result.success:
            full_text = result.full_text
            # Update DB with extracted text
            update_document_text(doc.id, full_text, chunk_count=0)

            # Chunk and embed
            chunk_count = load_and_index_document(
                project_id=project_id,
                document_id=doc.id,
                text=full_text,
                metadata={
                    "filename": uploaded_file.name,
                    "doc_type": doc_type,
                    "document_id": doc.id,
                },
            )

            # Update chunk count
            from core.database import update_document_text
            update_document_text(doc.id, full_text, chunk_count=chunk_count)
            st.success(f"✅ {uploaded_file.name} 处理完成！({chunk_count} 个向量块)")
        else:
            from core.database import update_document_status
            update_document_status(doc.id, "failed", result.error)
            st.error(f"解析失败: {result.error}")

    except Exception as e:
        st.error(f"上传处理失败: {str(e)}")
