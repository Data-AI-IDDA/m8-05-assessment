"""
Streamlit chat UI for LLM Study Buddy.

Run with:
    pip install -r requirements.txt
    streamlit run app.py
"""

import os

import streamlit as st
from dotenv import load_dotenv

from llm_service import ChatService

load_dotenv()

st.set_page_config(page_title="LLM Study Buddy", page_icon="🤖")
st.title("🤖 LLM Study Buddy")
st.caption("Ask me anything about prompting, Gemini, Ollama, evaluation, safety, or tokens!")

# ---------------------------------------------------------------------------
# Sidebar — settings and token usage
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Settings")

    # Temperature slider
    temperature = st.slider("Temperature", 0.0, 1.5, 0.4, 0.1,
                            help="Higher = more creative, lower = more focused")

    # Model selector — respects MODEL from .env if it's in the list
    _model_options = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
    _env_model = os.environ.get("MODEL", "gemini-2.0-flash")
    _default_index = _model_options.index(_env_model) if _env_model in _model_options else 0
    model_choice = st.selectbox(
        "Model",
        options=_model_options,
        index=_default_index,
        help="gemini-2.0-flash is free-tier friendly"
    )

    st.divider()

    # Clear chat button
    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.pop("service", None)
        st.session_state.pop("messages", None)
        st.rerun()

    st.divider()

    # Token usage display (updated after each response)
    st.subheader("📊 Token Usage")
    token_placeholder = st.empty()

# ---------------------------------------------------------------------------
# Session state — persist the ChatService and message list across reruns
# ---------------------------------------------------------------------------
if "service" not in st.session_state:
    try:
        st.session_state.service = ChatService(model=model_choice, temperature=temperature)
    except ValueError as e:
        st.error(str(e))
        st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

service: ChatService = st.session_state.service
# Update temperature and model if the user changed the sidebar controls
service.temperature = temperature
service.model = model_choice

# ---------------------------------------------------------------------------
# Render conversation history
# ---------------------------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------------------------------------------------------------------
# Handle a new user message
# ---------------------------------------------------------------------------
if prompt := st.chat_input("Ask about LLMs, prompting, Gemini, Ollama…"):
    # Show user message immediately
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Stream the assistant's reply
    with st.chat_message("assistant"):
        reply = st.write_stream(service.stream(prompt))

    # Save the complete reply to history
    st.session_state.messages.append({"role": "assistant", "content": reply})

# ---------------------------------------------------------------------------
# Update token usage in the sidebar
# ---------------------------------------------------------------------------
approx_note = " *(approx.)*" if service._tokens_are_approximate else ""
token_placeholder.markdown(
    f"**Input tokens:** {service.total_input_tokens}{approx_note}  \n"
    f"**Output tokens:** {service.total_output_tokens}{approx_note}"
)
if service._tokens_are_approximate:
    st.sidebar.caption("⚠️ Token counts are approximate (Gemini metadata unavailable)")
