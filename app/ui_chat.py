"""Simplified chat-only UI.

A thin shell over ``app/ui.py`` that exposes just the "Ask the Data" chat,
with no navigation/tabs. It reuses the real chat code by importing it, so the
full app (``streamlit run app/ui.py``) is untouched and stays the source of
truth. Importing ``app.ui`` also runs its module-level ``set_page_config`` and
CSS injection, so this file must NOT call ``set_page_config`` again.

Run with:
    streamlit run app/ui_chat.py
"""

import os
import sys

import streamlit as st

# Ensure the project root is importable when run as `streamlit run app/ui_chat.py`.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.ui import (  # noqa: E402  (import triggers ui.py page config + CSS)
    _apply_secrets_to_env,
    _has_ai_config,
    _render_header,
    render_chat,
)


def main() -> None:
    _apply_secrets_to_env()
    _render_header()

    with st.sidebar:
        st.markdown("**ATHL Data Platform**")
        st.write("Runtime status")
        st.write(f"AI configured: {'yes' if _has_ai_config() else 'no'}")
        st.write(f"DB_ENV: `{os.getenv('DB_ENV', 'local')}`")

    render_chat()


if __name__ == "__main__":
    main()
