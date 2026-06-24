"""
Streamlit chat UI for the ML/MLOps Study Buddy.
Run with:  streamlit run app.py
"""

import streamlit as st
from llm_service import ChatService

st.set_page_config(page_title="ML/MLOps Study Buddy", page_icon="🤖")
st.title("🤖 ML/MLOps Study Buddy")
st.caption("Ask me anything about deep learning, MLOps, Docker, LLMs, and the Ironhack curriculum.")

# --- Sidebar -----------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Settings")
    temperature = st.slider("Temperature", 0.0, 1.5, 0.4, 0.1)
    st.caption("Lower = more focused. Higher = more creative.")
    if st.button("🗑️ Clear chat"):
        st.session_state.pop("service", None)
        st.session_state.pop("messages", None)
        st.rerun()

# --- State -------------------------------------------------------------
if "service" not in st.session_state:
    st.session_state.service = ChatService(temperature=temperature)
if "messages" not in st.session_state:
    st.session_state.messages = []

service: ChatService = st.session_state.service
service.temperature = temperature

# --- Render history ----------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- New user turn -----------------------------------------------------
if prompt := st.chat_input("Ask a question about ML or MLOps…"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        reply = st.write_stream(service.stream(prompt))

    st.session_state.messages.append({"role": "assistant", "content": reply})

# --- Token usage in sidebar --------------------------------------------
with st.sidebar:
    st.divider()
    st.caption(f"📊 Tokens in: {service.total_input_tokens}")
    st.caption(f"📊 Tokens out: {service.total_output_tokens}")