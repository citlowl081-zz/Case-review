"""Main Streamlit app — sidebar navigation + page routing + Q&A panel."""
import streamlit as st
from core.database import get_all_projects, get_project, create_project, delete_project
from streamlit_app.project_page import render_project_page
from streamlit_app.subject_page import render_subject_page
from streamlit_app.review_page import render_review_page
from streamlit_app.chat_panel import render_chat_panel


def main():
    """Main app with sidebar + main content + right Q&A panel."""
    # ── Session State Init ──
    defaults = {
        "page": "home",
        "selected_project_id": None,
        "selected_subject_id": None,
        "active_report_id": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # ── Three-column layout ──
    sidebar_col, main_col, chat_col = st.columns([1.5, 4, 2.5])

    # ── Left: Sidebar ──
    with sidebar_col:
        _render_sidebar()

    # ── Center: Main content ──
    with main_col:
        page = st.session_state.page
        if page == "home":
            _render_home()
        elif page == "project":
            render_project_page()
        elif page == "subject":
            render_subject_page()
        elif page == "review":
            render_review_page()
        else:
            _render_home()

    # ── Right: Q&A Panel ──
    with chat_col:
        render_chat_panel()


def _render_sidebar():
    """Render the left sidebar with navigation."""
    st.title("🏥 临床试验")
    st.caption("病历质控系统 v1.0")

    st.divider()

    # Navigation
    if st.button("🏠 首页", use_container_width=True,
                 type="primary" if st.session_state.page == "home" else "secondary"):
        st.session_state.page = "home"
        st.session_state.selected_project_id = None
        st.session_state.selected_subject_id = None
        st.rerun()

    if st.button("📁 项目管理", use_container_width=True,
                 type="primary" if st.session_state.page == "project" else "secondary"):
        st.session_state.page = "project"
        st.rerun()

    # Show subjects if project selected
    if st.session_state.selected_project_id:
        p = get_project(st.session_state.selected_project_id)
        if p:
            st.caption(f"📌 {p.name}")

        if st.button("👤 受试者管理", use_container_width=True,
                     type="primary" if st.session_state.page == "subject" else "secondary"):
            st.session_state.page = "subject"
            st.rerun()

        if st.button("📋 开始审核", use_container_width=True,
                     type="primary" if st.session_state.page == "review" else "secondary"):
            st.session_state.page = "review"
            st.rerun()

    st.divider()

    # Project list quick nav
    st.caption("── 项目列表 ──")
    projects = get_all_projects()
    for p in projects[:10]:
        selected = st.session_state.get("selected_project_id") == p.id
        label = f"{'📍' if selected else '  '} {p.name[:25]}"
        if st.button(label, key=f"projnav_{p.id}", use_container_width=True,
                     type="secondary"):
            st.session_state.selected_project_id = p.id
            st.session_state.selected_subject_id = None
            st.session_state.page = "project"
            st.rerun()


def _render_home():
    """Home page content."""
    st.title("🏥 临床试验病历自动质控与澄清生成系统")
    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("项目数", len(get_all_projects()))
    with col2:
        st.metric("审核引擎", "9 个 Agent")
    with col3:
        st.metric("支持格式", "PDF/Word/Excel/TXT")

    st.markdown("---")

    # Quick create project
    st.subheader("📁 快速创建项目")
    with st.form("quick_create_project", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("项目名称 *", placeholder="如: XYZ-001 III期临床试验")
        with col2:
            proto = st.text_input("方案编号", placeholder="如: XYZ-001-V3.0")
        sponsor = st.text_input("申办方", placeholder="如: XX制药有限公司")

        if st.form_submit_button("创建项目", type="primary", use_container_width=True):
            if not name.strip():
                st.error("请输入项目名称")
            else:
                p = create_project(name=name.strip(), protocol_number=proto.strip(), sponsor=sponsor.strip())
                st.success(f"项目 '{p.name}' 创建成功！")
                st.session_state.selected_project_id = p.id
                st.session_state.page = "project"
                st.rerun()

    # Project list
    st.subheader("📋 项目列表")
    projects = get_all_projects()
    if not projects:
        st.info("暂无项目，请在上方创建第一个项目")
    else:
        cols = st.columns(3)
        for i, p in enumerate(projects):
            with cols[i % 3]:
                with st.container(border=True):
                    st.markdown(f"**{p.name}**")
                    if p.protocol_number:
                        st.caption(f"方案: {p.protocol_number}")
                    if p.sponsor:
                        st.caption(f"申办方: {p.sponsor}")
                    st.caption(f"创建: {p.created_at[:10] if p.created_at else ''}")

                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("📂 打开", key=f"open_{p.id}", use_container_width=True):
                            st.session_state.selected_project_id = p.id
                            st.session_state.page = "project"
                            st.rerun()
                    with c2:
                        if st.button("🗑️ 删除", key=f"del_{p.id}", use_container_width=True):
                            delete_project(p.id)
                            st.rerun()
