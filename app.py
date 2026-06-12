"""
Streamlit chat UI for the LLM chat micro-service.

STARTER skeleton. Run with:

    pip install -r requirements.txt
    streamlit run app.py

Requirements this file should satisfy (see README):
  - a chat interface using st.chat_message / st.chat_input
  - conversation history visible across turns
  - streaming responses (strongly preferred)
  - one small control (model / temperature picker, or "clear chat")
"""

import streamlit as st

from llm_service import ChatService, ConfigError

st.set_page_config(page_title="Study Buddy — Code Explainer", page_icon="💬")
st.title("💬 Study Buddy — Python & ML Code Explainer")
st.caption("Paste Python/ML code and I'll explain it. Ask follow-ups too.")

# --- Sidebar control (Requirement: one small control) ----------------------
with st.sidebar:
    st.header("Settings")
    temperature = st.slider("Temperature", 0.0, 1.5, 0.4, 0.1)
    # TODO (optional): add a model picker (hosted vs local).
    if st.button("Clear chat"):
        st.session_state.pop("service", None)
        st.session_state.pop("messages", None)
        st.rerun()

# --- State -----------------------------------------------------------------
if "service" not in st.session_state:
    try:
        st.session_state.service = ChatService(temperature=temperature)
    except ConfigError as exc:
        st.error(str(exc))
        st.stop()
if "messages" not in st.session_state:
    st.session_state.messages = []

service: ChatService = st.session_state.service
service.temperature = temperature

# --- Render history --------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Handle a new user turn ------------------------------------------------
if prompt := st.chat_input("Type a message…"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Streaming: st.write_stream consumes a generator of text chunks.
        # TODO: make ChatService.stream() actually stream from the model.
        reply = st.write_stream(service.stream(prompt))

    st.session_state.messages.append({"role": "assistant", "content": reply})

# --- Cost visibility (Requirement: token usage tracked) --------------------
with st.sidebar:
    st.caption(
        f"Tokens — in: {service.total_input_tokens} / "
        f"out: {service.total_output_tokens}"
    )
