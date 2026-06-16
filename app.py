"""
Streamlit chat UI for the LLM chat micro-service.
Runs with:
    streamlit run app.py
"""

import streamlit as st
from llm_service import ChatService

st.set_page_config(page_title="AI Study Buddy", page_icon="🎓")
st.title("🎓 Deep Learning & AI Study Buddy")
st.caption("Review your Computer Vision (CNNs, YOLO) and LLM concepts with active recall quiz questions!")

# --- Sidebar control (Requirement: one small control) ----------------------
with st.sidebar:
    st.header("Settings")
    temperature = st.slider("Temperature", 0.0, 1.5, 0.4, 0.1)
    
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
if prompt := st.chat_input("Ask a question about CNNs, YOLO, or LLMs..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Streaming: consumes our updated stream() generator live
        reply = st.write_stream(service.stream(prompt))

    st.session_state.messages.append({"role": "assistant", "content": reply})

# --- Cost visibility (Requirement: token usage tracked) --------------------
with st.sidebar:
    st.divider()
    st.markdown("### Session Usage Metrics")
    st.caption(
        f"**Tokens In:** {service.total_input_tokens}  \n"
        f"**Tokens Out:** {service.total_output_tokens}"
    )