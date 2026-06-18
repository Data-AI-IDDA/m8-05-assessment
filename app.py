"""
IT Study Buddy — Premium Streamlit chat UI with Dark / Light mode.

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from llm_service import ChatService

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="IT Study Buddy",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

if "service" not in st.session_state:
    st.session_state.service = ChatService()

if "messages" not in st.session_state:
    st.session_state.messages: list[dict[str, str]] = []

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True  # default to dark

service: ChatService = st.session_state.service
dark: bool = st.session_state.dark_mode

# ---------------------------------------------------------------------------
# Theme palette
# ---------------------------------------------------------------------------

if dark:
    T = {
        # Main canvas
        "bg":           "#0e0e14",
        "bg2":          "#16161e",
        # Text
        "text":         "#e0e0ec",
        "text_muted":   "#7b7b9a",
        "text_dim":     "#5a5a78",
        # Sidebar
        "sb_bg":        "#111118",
        "sb_border":    "#1f1f2e",
        "sb_card":      "#1a1a24",
        "sb_card_bdr":  "#2a2a3c",
        # Bubbles
        "user_bg":      "#6c6cf0",
        "user_text":    "#ffffff",
        "asst_bg":      "#1a1a24",
        "asst_text":    "#d4d4e0",
        "asst_border":  "#2a2a3c",
        # Input box
        "input_bg":     "#16161e",
        "input_border": "#2a2a3c",
        "input_text":   "#e0e0ec",
        "input_focus":  "#6c6cf0",
        # Welcome
        "wt_title":     "#e8e8f5",
        "wt_sub":       "#7878a0",
        # Example buttons
        "ex_bg":        "#1a1a24",
        "ex_border":    "#2a2a3c",
        "ex_text":      "#c0c0d8",
        "ex_hover_bdr": "#6c6cf0",
        # Toggle button
        "toggle_bg":    "#1a1a24",
        "toggle_bdr":   "#2a2a3c",
        "toggle_text":  "#c0c0d8",
        # Metric
        "metric_val":   "#e8e8f5",
        "metric_lbl":   "#5a5a78",
    }
else:
    T = {
        # Main canvas
        "bg":           "#f7f9fb",
        "bg2":          "#ffffff",
        # Text
        "text":         "#1a1a2e",
        "text_muted":   "#6e6e8a",
        "text_dim":     "#9090a8",
        # Sidebar
        "sb_bg":        "#1a1a22",
        "sb_border":    "#2e2e3a",
        "sb_card":      "#25252f",
        "sb_card_bdr":  "#35354a",
        # Bubbles
        "user_bg":      "#0f0f13",
        "user_text":    "#ffffff",
        "asst_bg":      "#ffffff",
        "asst_text":    "#1a1a2e",
        "asst_border":  "#e8eaf0",
        # Input box
        "input_bg":     "#ffffff",
        "input_border": "#e0e3eb",
        "input_text":   "#1a1a2e",
        "input_focus":  "#6c6cf0",
        # Welcome
        "wt_title":     "#0f0f1a",
        "wt_sub":       "#7878a0",
        # Example buttons
        "ex_bg":        "#ffffff",
        "ex_border":    "#e0e3eb",
        "ex_text":      "#2a2a42",
        "ex_hover_bdr": "#6c6cf0",
        # Toggle button
        "toggle_bg":    "#ffffff",
        "toggle_bdr":   "#e0e3eb",
        "toggle_text":  "#2a2a42",
        # Metric
        "metric_val":   "#e8e8f5",
        "metric_lbl":   "#5a5a78",
    }

# ---------------------------------------------------------------------------
# CSS — dynamically themed
# ---------------------------------------------------------------------------

st.markdown(
    f"""
    <style>
    /* ── Font ───────────────────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}

    /* ── Main canvas ────────────────────────────────────────────────────── */
    .stApp {{
        background: {T["bg"]} !important;
        color: {T["text"]} !important;
    }}

    .block-container {{
        max-width: 860px !important;
        padding: 0.5rem 1.5rem 6rem !important;
        margin: 0 auto !important;
    }}

    /* ── Hide Streamlit chrome ──────────────────────────────────────────── */
    #MainMenu, footer {{ visibility: hidden; }}
    header {{ visibility: visible !important; }}

    /* ── Top bar theme toggle ──────────────────────────────────────────── */
    .theme-bar {{
        display: flex;
        justify-content: flex-end;
        padding: 0.5rem 0 0.2rem;
        position: sticky;
        top: 0;
        z-index: 999;
    }}

    /* ── Sidebar ────────────────────────────────────────────────────────── */
    [data-testid="stSidebar"] {{
        background: {T["sb_bg"]} !important;
        border-right: 1px solid {T["sb_border"]} !important;
    }}
    [data-testid="stSidebar"] * {{
        color: #d4d4e0 !important;
    }}

    .sb-logo {{
        display: flex; align-items: center; gap: 10px;
        padding: 1.2rem 0 0.4rem;
    }}
    .sb-logo-icon {{
        width: 36px; height: 36px;
        background: linear-gradient(135deg, #6c6cf0, #a78bfa);
        border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.1rem;
    }}
    .sb-logo-text {{ line-height: 1.2; }}
    .sb-logo-name {{
        font-size: 1rem; font-weight: 700; color: #ffffff !important;
    }}
    .sb-logo-sub {{
        font-size: 0.72rem; color: #7b7b9a !important; margin-top: 1px;
    }}

    .sb-label {{
        font-size: 0.67rem; font-weight: 600; letter-spacing: 0.08em;
        text-transform: uppercase; color: #5a5a78 !important;
        margin: 1.4rem 0 0.45rem;
    }}

    .sb-model-badge {{
        background: {T["sb_card"]};
        border: 1px solid {T["sb_card_bdr"]};
        border-radius: 10px; padding: 8px 12px;
        font-size: 0.82rem; font-weight: 500; color: #b0b0cc !important;
        display: flex; align-items: center; gap: 8px;
    }}
    .sb-model-dot {{
        width: 7px; height: 7px; background: #4ade80;
        border-radius: 50%; flex-shrink: 0;
    }}

    /* Sidebar metrics */
    /* ── Compact token cards ────────────────────────────────────────────── */
    .token-row {{
        display: flex; gap: 8px; margin-top: 6px;
    }}
    .token-card {{
        flex: 1;
        background: {T["sb_card"]};
        border: 1px solid {T["sb_card_bdr"]};
        border-radius: 8px;
        padding: 8px 10px;
        display: flex; align-items: center; gap: 8px;
    }}
    .token-icon {{
        width: 28px; height: 28px;
        border-radius: 6px;
        display: flex; align-items: center; justify-content: center;
        font-size: 0.75rem; flex-shrink: 0;
    }}
    .token-icon.inp {{ background: rgba(108,108,240,0.15); }}
    .token-icon.out {{ background: rgba(74,222,128,0.15); }}
    .token-info {{ line-height: 1.2; }}
    .token-val {{
        font-size: 0.95rem; font-weight: 700;
        color: {T["metric_val"]} !important;
        letter-spacing: -0.01em;
    }}
    .token-lbl {{
        font-size: 0.6rem; font-weight: 500;
        color: {T["metric_lbl"]} !important;
        text-transform: uppercase; letter-spacing: 0.06em;
    }}

    [data-testid="stSidebar"] hr {{
        border-color: {T["sb_border"]} !important; margin: 1.1rem 0;
    }}

    /* Sidebar button */
    [data-testid="stSidebar"] .stButton > button {{
        width: 100%;
        background: transparent !important;
        border: 1px solid {T["sb_card_bdr"]} !important;
        border-radius: 10px !important;
        color: #8080a0 !important;
        font-size: 0.82rem !important; font-weight: 500 !important;
        padding: 0.55rem 1rem !important;
        transition: background 0.18s, color 0.18s, border-color 0.18s !important;
        min-height: unset !important;
        text-align: center !important;
        transform: none !important;
        box-shadow: none !important;
    }}
    [data-testid="stSidebar"] .stButton > button:hover {{
        background: #2e2e3c !important;
        border-color: #4a4a62 !important;
        color: #c0c0d8 !important;
    }}

    /* ── Remove default st.chat_message chrome & set Assistant styling ── */
    [data-testid="stChatMessage"] {{
        background: {T["asst_bg"]} !important;
        border: 1px solid {T["asst_border"]} !important;
        border-radius: 16px !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05) !important;
        padding: 14px 18px !important;
        margin-bottom: 14px !important;
        max-width: 85% !important;
        margin-right: auto !important;
        width: fit-content !important;
    }}
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li,
    [data-testid="stChatMessage"] span,
    [data-testid="stChatMessage"] code,
    [data-testid="stChatMessage"] div {{
        color: {T["asst_text"]} !important;
    }}
    [data-testid="stChatMessage"] pre {{
        background: {"#111118" if dark else "#f4f4f8"} !important;
        border-radius: 8px !important;
    }}
    [data-testid="stChatMessage"] pre code {{
        color: {"#c8c8e0" if dark else "#1a1a2e"} !important;
    }}

    /* ── User Chat Message (Right Aligned Pill) ─────────────────────────── */
    [data-testid="stChatMessage"]:has(img[alt="user"]),
    [data-testid="stChatMessage"]:has(img[alt="user avatar"]),
    [data-testid="stChatMessage"]:has([data-testid*="user"]),
    [data-testid="stChatMessage"]:has([data-testid*="User"]) {{
        flex-direction: row-reverse !important;
        background: {T["user_bg"]} !important;
        border: none !important;
        border-radius: 22px 22px 4px 22px !important;
        box-shadow: 0 4px 16px rgba(108,108,240,0.2) !important;
        max-width: 75% !important;
        margin-left: auto !important;
        margin-right: 0 !important;
        width: fit-content !important;
    }}

    [data-testid="stChatMessage"]:has(img[alt="user"]) p,
    [data-testid="stChatMessage"]:has(img[alt="user avatar"]) p,
    [data-testid="stChatMessage"]:has([data-testid*="user"]) p,
    [data-testid="stChatMessage"]:has([data-testid*="User"]) p,
    [data-testid="stChatMessage"]:has(img[alt="user"]) li,
    [data-testid="stChatMessage"]:has(img[alt="user avatar"]) li,
    [data-testid="stChatMessage"]:has([data-testid*="user"]) li,
    [data-testid="stChatMessage"]:has([data-testid*="User"]) li,
    [data-testid="stChatMessage"]:has(img[alt="user"]) span,
    [data-testid="stChatMessage"]:has(img[alt="user avatar"]) span,
    [data-testid="stChatMessage"]:has([data-testid*="user"]) span,
    [data-testid="stChatMessage"]:has([data-testid*="User"]) span {{
        color: {T["user_text"]} !important;
    }}

    [data-testid="stChatMessage"]:has(img[alt="user"]) [data-testid="stChatMessageAvatar"],
    [data-testid="stChatMessage"]:has(img[alt="user avatar"]) [data-testid="stChatMessageAvatar"],
    [data-testid="stChatMessage"]:has([data-testid*="user"]) [data-testid="stChatMessageAvatar"],
    [data-testid="stChatMessage"]:has([data-testid*="User"]) [data-testid="stChatMessageAvatar"] {{
        background: {T["user_bg"]} !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
    }}

    /* ── Custom bubble wrappers ────────────────────────────────────────── */
    .msg-row {{
        display: flex; align-items: flex-end;
        margin-bottom: 18px; gap: 10px;
        animation: fadeUp 0.22s ease both;
    }}
    @keyframes fadeUp {{
        from {{ opacity: 0; transform: translateY(8px); }}
        to   {{ opacity: 1; transform: translateY(0); }}
    }}
    .msg-row.user {{ flex-direction: row-reverse; }}

    .bubble {{
        max-width: 72%; padding: 13px 18px;
        line-height: 1.65; font-size: 0.92rem; word-break: break-word;
    }}
    .bubble.user {{
        background: {T["user_bg"]};
        color: {T["user_text"]};
        border-radius: 22px 22px 4px 22px;
        box-shadow: 0 4px 16px rgba(108,108,240,0.25);
    }}
    .bubble.assistant {{
        background: {T["asst_bg"]};
        color: {T["asst_text"]};
        border: 1px solid {T["asst_border"]};
        border-radius: 4px 22px 22px 22px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }}

    .avatar {{
        width: 34px; height: 34px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 0.85rem; flex-shrink: 0;
    }}
    .avatar.user {{
        background: {T["user_bg"]}; color: #ffffff;
        font-weight: 600; font-size: 0.72rem;
    }}
    .avatar.assistant {{
        background: linear-gradient(135deg, #6c6cf0, #a78bfa);
        color: #fff; font-size: 1rem;
    }}

    /* ── Chat input ────────────────────────────────────────────────────── */
    [data-testid="stChatInput"] > div {{
        background: {T["input_bg"]} !important;
        border: 1.5px solid {T["input_border"]} !important;
        border-radius: 28px !important;
        box-shadow: 0 4px 24px rgba(0,0,0,{"0.18" if dark else "0.06"}) !important;
        transition: box-shadow 0.2s, border-color 0.2s !important;
    }}
    [data-testid="stChatInput"] > div:focus-within {{
        border-color: {T["input_focus"]} !important;
        box-shadow: 0 0 0 3px rgba(108,108,240,0.15),
                    0 4px 24px rgba(0,0,0,{"0.18" if dark else "0.06"}) !important;
    }}
    [data-testid="stChatInput"] textarea {{
        font-family: 'Inter', sans-serif !important;
        font-size: 0.9rem !important;
        color: {T["input_text"]} !important;
        caret-color: {T["input_text"]} !important;
    }}
    [data-testid="stChatInput"] textarea::placeholder {{
        color: {T["text_muted"]} !important;
        opacity: 1 !important;
    }}
    /* Send button inside input */
    [data-testid="stChatInput"] button {{
        color: {"#ffffff" if dark else "#0f0f13"} !important;
        background: transparent !important;
    }}
    [data-testid="stChatInput"] button:hover {{
        color: {T["input_focus"]} !important;
    }}
    [data-testid="stChatInput"] button svg {{
        fill: {"#ffffff" if dark else "#0f0f13"} !important;
        stroke: {"#ffffff" if dark else "#0f0f13"} !important;
    }}
    [data-testid="stChatInput"] button:hover svg {{
        fill: {T["input_focus"]} !important;
        stroke: {T["input_focus"]} !important;
    }}

    /* ── Welcome screen ────────────────────────────────────────────────── */
    .welcome-wrap {{
        text-align: center; padding: 4rem 1rem 2.5rem;
    }}
    .welcome-icon {{
        width: 64px; height: 64px;
        background: linear-gradient(135deg, #6c6cf0, #a78bfa);
        border-radius: 18px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.8rem; margin: 0 auto 1.2rem;
        box-shadow: 0 8px 24px rgba(108,108,240,0.28);
    }}
    .welcome-title {{
        font-size: 2.1rem; font-weight: 700;
        color: {T["wt_title"]}; letter-spacing: -0.03em;
        margin-bottom: 0.6rem;
    }}
    .welcome-sub {{
        font-size: 0.97rem; color: {T["wt_sub"]};
        max-width: 520px; margin: 0 auto 2.5rem; line-height: 1.7;
    }}
    .welcome-hint {{
        font-size: 0.78rem; color: {T["text_muted"]};
        margin-bottom: 0.9rem; text-transform: uppercase;
        letter-spacing: 0.08em; font-weight: 600;
    }}

    /* Example prompt buttons (main area) */
    section:not([data-testid="stSidebar"]) .stButton > button {{
        background: {T["ex_bg"]} !important;
        border: 1.5px solid {T["ex_border"]} !important;
        border-radius: 14px !important;
        color: {T["ex_text"]} !important;
        font-size: 0.83rem !important; font-weight: 500 !important;
        padding: 0.7rem 0.9rem !important;
        text-align: left !important; line-height: 1.4 !important;
        transition: border-color 0.18s, box-shadow 0.18s, transform 0.12s !important;
        box-shadow: 0 1px 4px rgba(0,0,0,{"0.12" if dark else "0.04"}) !important;
        height: auto !important; min-height: 60px !important;
        white-space: normal !important;
    }}
    section:not([data-testid="stSidebar"]) .stButton > button:hover {{
        border-color: {T["ex_hover_bdr"]} !important;
        box-shadow: 0 4px 16px rgba(108,108,240,0.15) !important;
        transform: translateY(-2px) !important;
    }}

    /* ── Theme toggle (top bar) ────────────────────────────────────────── */
    .theme-toggle-row {{
        display: flex;
        justify-content: flex-end;
        padding: 0 0 0.5rem;
    }}
    .theme-toggle-row .stButton > button {{
        background: {T["toggle_bg"]} !important;
        border: 1.5px solid {T["toggle_bdr"]} !important;
        border-radius: 999px !important;
        color: {T["toggle_text"]} !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        padding: 0.4rem 1.1rem !important;
        min-height: unset !important;
        height: auto !important;
        box-shadow: none !important;
        transform: none !important;
        transition: background 0.18s, border-color 0.18s !important;
    }}
    .theme-toggle-row .stButton > button:hover {{
        border-color: #6c6cf0 !important;
        background: {"#22222e" if dark else "#eef0f4"} !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EXAMPLE_PROMPTS: list[str] = [
    "🔍 Explain binary search with an example",
    "🐳 What is Docker and why is it used?",
    "🌐 Explain REST APIs to a beginner",
    "🗄️ Difference between SQL and NoSQL",
    "🤖 How does machine learning work?",
    "🐧 Linux file permissions explained",
]

# ---------------------------------------------------------------------------
# Top bar — theme toggle
# ---------------------------------------------------------------------------

with st.container():
    cols = st.columns([8, 1])
    with cols[1]:
        toggle_label = "☀️ Light" if dark else "🌙 Dark"
        if st.button(toggle_label, key="theme_toggle", use_container_width=True):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()

# Wrap the toggle row with a CSS class
st.markdown(
    """<style>
    /* Target the first container's columns to act as the toggle row */
    .block-container > div:first-child .stButton > button {
        background: transparent !important;
        border-radius: 999px !important;
        min-height: unset !important;
        height: auto !important;
        padding: 0.35rem 1rem !important;
    }
    </style>""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown(
        """
        <div class="sb-logo">
            <div class="sb-logo-icon">🤖</div>
            <div class="sb-logo-text">
                <div class="sb-logo-name">IT Study Buddy</div>
                <div class="sb-logo-sub">Powered by Local Llama 3.2</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown('<div class="sb-label">Active Model</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="sb-model-badge">
            <div class="sb-model-dot"></div>
            {service.model}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown('<div class="sb-label">Settings</div>', unsafe_allow_html=True)
    new_temp = st.slider("Temperature", min_value=0.0, max_value=1.0, value=service.temperature, step=0.1)
    if new_temp != service.temperature:
        service.temperature = new_temp

    st.divider()

    st.markdown('<div class="sb-label">Token Usage</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="token-row">
            <div class="token-card">
                <div class="token-icon inp">📥</div>
                <div class="token-info">
                    <div class="token-val">{service.total_input_tokens:,}</div>
                    <div class="token-lbl">Input</div>
                </div>
            </div>
            <div class="token-card">
                <div class="token-icon out">📤</div>
                <div class="token-info">
                    <div class="token-val">{service.total_output_tokens:,}</div>
                    <div class="token-lbl">Output</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    if st.button("🗑️  Clear Chat", use_container_width=True):
        st.session_state.pop("service", None)
        st.session_state.pop("messages", None)
        st.rerun()

# ---------------------------------------------------------------------------
# Render conversation history
# ---------------------------------------------------------------------------

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------------------------------------------------------------------
# Welcome / empty-state
# ---------------------------------------------------------------------------

if not st.session_state.messages:
    st.markdown(
        f"""
        <div class="welcome-wrap">
            <div class="welcome-icon">🤖</div>
            <div class="welcome-title">IT Study Buddy</div>
            <p class="welcome-sub">
                Ask anything about programming, software engineering, AI,
                databases, cloud computing, Linux, networking, and computer science.
            </p>
            <div class="welcome-hint">✦ Try an example</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    for i, prompt_text in enumerate(EXAMPLE_PROMPTS):
        target_col = col1 if i % 2 == 0 else col2
        with target_col:
            if st.button(prompt_text, use_container_width=True, key=f"ex_{i}"):
                st.session_state.messages.append(
                    {"role": "user", "content": prompt_text}
                )
                st.rerun()

# ---------------------------------------------------------------------------
# Chat input → stream → store
# ---------------------------------------------------------------------------

if user_input := st.chat_input("Ask me anything about IT & Computer Science…"):
    # Render user message live
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Stream assistant reply (st.chat_message needed for write_stream)
    with st.chat_message("assistant"):
        reply: str = st.write_stream(service.stream(user_input))

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()
