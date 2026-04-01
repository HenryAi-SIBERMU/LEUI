import os
import gettext
import streamlit as st

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
LOCALE_DIR = os.path.join(PROJECT_ROOT, "locales")

def init_lang():
    if 'lang' not in st.session_state:
        st.session_state.lang = 'id'

def set_lang(lang_code):
    st.session_state.lang = lang_code

def _(message):
    lang = st.session_state.get('lang', 'id')
    try:
        gettext._translations.clear()
        t = gettext.translation('messages', localedir=LOCALE_DIR, languages=[lang])
        return t.gettext(message)
    except FileNotFoundError:
        return message
