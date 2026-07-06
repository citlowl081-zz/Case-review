#!/usr/bin/env python3
"""Clinical Trial Medical Record QC System — Streamlit Entry Point.

Usage:
    streamlit run app.py
"""
import sys
import os

# Ensure project root is in path
_project_root = os.path.dirname(os.path.abspath(__file__))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import streamlit as st
from core.database import ensure_db
from streamlit_app.main import main


def login_screen():
    """Simple password gate — protect the entire app."""
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🏥 临床试验病历质控系统")
        st.caption("Clinical Trial QC System")
        st.markdown("---")
        password = st.text_input(
            "请输入访问密码",
            type="password",
            placeholder="输入密码后按回车",
            key="login_password",
        )

        # Read password from env
        expected = os.getenv("APP_PASSWORD", "qc2026")

        if password:
            if password == expected:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("密码错误，请重试")

        st.markdown("---")
        st.caption("提示：密码在 .env 文件的 APP_PASSWORD 中设置")
        st.caption("默认密码: qc2026（请尽快修改！）")


if __name__ == "__main__":
    st.set_page_config(
        page_title="临床试验病历质控系统",
        page_icon="🏥",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Initialize auth state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    ensure_db()

    # Gate: show login or main app
    if st.session_state.authenticated:
        main()
    else:
        login_screen()
