import streamlit as st


def hide_streamlit_ui():
    st.markdown(
        """
        <style>
        #MainMenu { display: none; }
        footer { display: none; }
        [data-testid="stDeployButton"] { display: none; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hide_sidebar():
    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"] { display: none; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def apply_theme(theme: str):
    if theme == "dark":
        st.markdown(
            """
            <style>
            :root {
              --hm-bg: #0E1117;
              --hm-bg2: #0B0F14;
              --hm-text: #FAFAFA;
              --hm-muted: rgba(250,250,250,0.72);
              --hm-card: #161B22;
              --hm-border: rgba(250,250,250,0.14);
              --hm-input: #0B1220;
              --hm-input-text: #FAFAFA;
              --hm-placeholder: rgba(250,250,250,0.48);
              --hm-primary: #4CAF50;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <style>
            :root {
              --hm-bg: #FFFFFF;
              --hm-bg2: #F6F7F9;
              --hm-text: #0E1117;
              --hm-muted: rgba(14,17,23,0.72);
              --hm-card: #FFFFFF;
              --hm-border: rgba(14,17,23,0.12);
              --hm-input: #FFFFFF;
              --hm-input-text: #0E1117;
              --hm-placeholder: rgba(14,17,23,0.40);
              --hm-primary: #2E7D32;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <style>
        html, body, #root {
          background-color: var(--hm-bg) !important;
          color: var(--hm-text) !important;
        }
        .stApp { color: var(--hm-text); }
        [data-testid="stApp"] { background-color: var(--hm-bg) !important; }
        [data-testid="stAppViewContainer"] { background-color: var(--hm-bg); }
        [data-testid="stSidebarContent"] { background-color: var(--hm-bg2); }
        [data-testid="stSidebar"] { border-right: 1px solid var(--hm-border); }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stHeader"] * { color: var(--hm-text) !important; }
        [data-testid="stHeader"] svg { fill: var(--hm-text) !important; }
        [data-testid="stBottomBlockContainer"],
        [data-testid="stBottomContainer"],
        [data-testid="stBottom"] {
          background: var(--hm-bg) !important;
          border-top: 1px solid var(--hm-border) !important;
        }
        [data-testid="stBottomBlockContainer"] *,
        [data-testid="stBottomContainer"] *,
        [data-testid="stBottom"] * {
          background-color: transparent !important;
        }

        .stApp, .stApp p, .stApp span, .stApp label, .stApp li,
        .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
          color: var(--hm-text);
        }
        .stApp small, .stApp .stCaption, .stApp [data-testid="stCaptionContainer"] {
          color: var(--hm-muted);
        }

        [data-testid="stChatMessage"] { background: transparent; }

        div[data-baseweb="input"] input,
        div[data-baseweb="textarea"] textarea {
          background-color: var(--hm-input) !important;
          color: var(--hm-input-text) !important;
          border-color: var(--hm-border) !important;
        }
        input:-webkit-autofill,
        input:-webkit-autofill:hover,
        input:-webkit-autofill:focus,
        textarea:-webkit-autofill,
        textarea:-webkit-autofill:hover,
        textarea:-webkit-autofill:focus {
          -webkit-box-shadow: 0 0 0px 1000px var(--hm-input) inset !important;
          -webkit-text-fill-color: var(--hm-input-text) !important;
          caret-color: var(--hm-input-text) !important;
          border-color: var(--hm-border) !important;
          transition: background-color 9999s ease-out 0s;
        }
        div[data-baseweb="input"] input::placeholder,
        div[data-baseweb="textarea"] textarea::placeholder {
          color: var(--hm-placeholder) !important;
        }
        div[data-baseweb="select"] > div {
          background-color: var(--hm-input) !important;
          border-color: var(--hm-border) !important;
        }
        div[data-baseweb="select"] * {
          color: var(--hm-input-text) !important;
        }

        details, summary {
          border-color: var(--hm-border) !important;
        }
        details > summary {
          background: var(--hm-card) !important;
        }
        details > div {
          background: transparent !important;
        }

        div.stButton > button:first-child {
          border-color: var(--hm-border) !important;
          background-color: var(--hm-card) !important;
          color: var(--hm-text) !important;
        }
        [data-testid="stFormSubmitButton"] button {
          border-color: var(--hm-border) !important;
          background-color: var(--hm-card) !important;
          color: var(--hm-text) !important;
        }
        div.stButton > button:first-child:hover {
          border-color: var(--hm-primary) !important;
          color: var(--hm-primary) !important;
        }
        [data-testid="stFormSubmitButton"] button:hover {
          border-color: var(--hm-primary) !important;
          color: var(--hm-primary) !important;
        }

        [data-testid="stChatInput"] { background: transparent !important; }
        [data-testid="stChatInput"] > div { background: transparent !important; }
        [data-testid="stChatInputContainer"],
        [data-testid="stChatInputContainer"] > div {
          background: var(--hm-bg) !important;
        }
        [data-testid="stChatInputContainer"] div,
        [data-testid="stChatInputContainer"] section,
        [data-testid="stChatInputContainer"] form {
          background: transparent !important;
        }
        [data-testid="stChatInput"] textarea {
          background-color: var(--hm-input) !important;
          color: var(--hm-input-text) !important;
        }
        [data-testid="stChatInput"] div[data-baseweb="textarea"] {
          border-color: var(--hm-border) !important;
        }
        [data-testid="stChatInput"] div[data-baseweb="textarea"]:focus-within {
          border-color: var(--hm-primary) !important;
          box-shadow: 0 0 0 1px var(--hm-primary) !important;
        }
        [data-testid="stChatInput"] button {
          background: var(--hm-card) !important;
          border-color: var(--hm-border) !important;
          color: var(--hm-text) !important;
        }
        [data-testid="stChatInput"] button:disabled {
          opacity: 0.6;
        }
        [data-testid="stChatInput"] button svg {
          fill: var(--hm-text) !important;
          color: var(--hm-text) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
