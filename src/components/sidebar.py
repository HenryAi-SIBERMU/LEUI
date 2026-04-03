"""Shared sidebar component — imported by all pages for consistent branding & nav."""
import streamlit as st
import os
from src.utils.i18n import init_lang, set_lang, _

def render_sidebar():
    st.markdown("""
    <style>
    .sidebar-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #66BB6A;
        text-align: center;
        padding-bottom: 20px;
        margin-bottom: 0px;
        border-bottom: 1px solid #ffffff11;
    }
    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        logo_path = os.path.join(base_dir, "ref", "Celios China-Indonesia Energy Transition.png")
        if os.path.exists(logo_path):
            st.image(logo_path, use_container_width=True)

        st.markdown('<div class="sidebar-title">CELIOS — Riset LEUI</div>', unsafe_allow_html=True)
        st.caption("Legal Enforcement Uncertainty Index")
        st.markdown("---")

        init_lang()
        st.markdown("**Language** / **Bahasa**")

        lang_options = {"id": "ID", "en": "EN"}
        current_lang = st.session_state.get('lang', 'id')
        current_idx = list(lang_options.keys()).index(current_lang)

        def switch_lang():
            selected = st.session_state.lang_radio
            set_lang(selected)

        st.radio(
            "Language",
            options=lang_options.keys(),
            format_func=lambda x: lang_options[x],
            index=current_idx,
            key="lang_radio",
            on_change=switch_lang,
            horizontal=True,
            label_visibility="collapsed"
        )
        st.markdown("---")

        # Navigation
        st.page_link("Dashboard.py", label="Dashboard", icon=None)

        st.markdown("### Resources")
        st.page_link("pages/1_Eksplorasi_Data.py", label="Eksplorasi Data", icon=None)
        st.page_link("pages/2_Dokumentasi_Riset.py", label="Dokumentasi Riset", icon=None)

        st.markdown("### Analisis")
        st.page_link("pages/3_H1_Inconsistency_Risk.py", label="H1: Inconsistency Risk", icon=None)

