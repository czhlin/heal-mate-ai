import re

import streamlit as st

_TEST_ID_SAFE_RE = re.compile(r"[^a-zA-Z0-9_-]+")


def test_id(value: str) -> None:
    safe = _TEST_ID_SAFE_RE.sub("-", (value or "").strip())
    st.markdown(
        f"<div data-testid='{safe}' style='width:1px;height:1px;opacity:0;position:fixed;left:-9999px;top:0;'></div>",
        unsafe_allow_html=True,
    )
