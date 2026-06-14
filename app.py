"""
ML Study Buddy — Next Level UI
ChatGPT-style Streamlit interface with clean UX and streaming support.
"""

from __future__ import annotations

import streamlit as st
from llm_service import ChatService

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="ML Study Buddy",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Minimal modern styling
# ─────────────────────────────────────────────

st.markdown(
    """
    <style>
        .stChatMessage {
            border-radius: 12px;
        }

        section[data-testid="stSidebar"] {
            padding-top: 1rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
# Sidebar (controls)
# ─────────────────────────────────────────────

with st.sidebar:
    st.title("⚙️ Controls")

    mode = st.selectbox(
        "Mode",
        ["Explain", "Quiz", "Learning Path"],
        help="Controls how the assistant responds"
    )

    temperature = st.slider(
        "Creativity",
        0.0,
        1.5,
        0.4,
        0.1
    )

    model_choice = st.selectbox(
        "Model",
        ["gemma3:4b", "llama3.2:3b", "qwen2.5:0.5b"],
    )

    st.markdown("---")

    if st.button("🗑️ Clear"):
        st.session_state.clear()
        st.rerun()

    st.caption("ML Study Buddy v2")

# ─────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────

if "service" not in st.session_state:
    st.session_state.service = ChatService(
        model=model_choice,
        temperature=temperature,
    )

service: ChatService = st.session_state.service

service.model = model_choice
service.temperature = temperature

if "messages" not in st.session_state:
    st.session_state.messages = []

# ─────────────────────────────────────────────
# Header (NO EMOJI)
# ─────────────────────────────────────────────

st.markdown(
    """
    <div style="
        text-align: center;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    ">
        Machine Learning Study Buddy
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div style="
        text-align: center;
        font-size: 1.2rem;
        opacity: 0.7;
        margin-bottom: 1.5rem;
    ">
        Your AI tutor for Machine Learning
    </div>
    """,
    unsafe_allow_html=True
)

# ─────────────────────────────────────────────
# Mode prompts
# ─────────────────────────────────────────────

MODE_PREFIX = {
    "Explain": "Explain clearly with a simple example:\n",
    "Quiz": "Create 3-5 quiz questions (do NOT give answers):\n",
    "Learning Path": "Create a structured step-by-step learning roadmap:\n",
}

# ─────────────────────────────────────────────
# Chat history
# ─────────────────────────────────────────────

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ─────────────────────────────────────────────
# Input
# ─────────────────────────────────────────────

prompt = st.chat_input("Ask anything about Machine Learning...")

if prompt:
    final_prompt = MODE_PREFIX[mode] + prompt

    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = st.write_stream(
            service.stream(final_prompt)
        )

    st.session_state.messages.append(
        {"role": "assistant", "content": response}
    )