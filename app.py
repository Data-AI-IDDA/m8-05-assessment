"""
Streamlit chat UI for the LLM chat micro-service.

Run with:
    streamlit run app.py
"""

import streamlit as st
from llm_service import ChatService

st.set_page_config(page_title="PyCoach -- Python Programming Tutor", page_icon=None)
st.title("PyCoach -- Python Programming Tutor")

# --- Sidebar control (Requirement: one small control) ----------------------
with st.sidebar:
    st.header("Settings")
    temperature = st.slider("Temperature", 0.0, 1.5, 0.4, 0.1)
    
    # Model configuration
    st.markdown("### Model Info")
    # Determine the model currently configured
    if "service" in st.session_state:
        backend_name = st.session_state.service.backend.upper()
        model_name = st.session_state.service.model
        st.info(f"Backend: {backend_name}\n\nModel: {model_name}")
    
    if st.button("Clear chat"):
        st.session_state.pop("service", None)
        st.session_state.pop("messages", None)
        st.rerun()

# --- State -----------------------------------------------------------------
if "service" not in st.session_state:
    st.session_state.service = ChatService(temperature=temperature)
if "messages" not in st.session_state:
    st.session_state.messages = []

service: ChatService = st.session_state.service
service.temperature = temperature

# --- Render history --------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Handle a new user turn ------------------------------------------------
if prompt := st.chat_input("Ask a Python question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # stream() returns a generator yielding chunks and updates token counts
        reply = st.write_stream(service.stream(prompt))

    st.session_state.messages.append({"role": "assistant", "content": reply})

# --- Cost visibility (Requirement: token usage tracked) --------------------
with st.sidebar:
    st.markdown("---")
    st.markdown("### Token Usage")
    st.metric(label="Input Tokens", value=service.total_input_tokens)
    st.metric(label="Output Tokens", value=service.total_output_tokens)
