"""
Streamlit chat UI for the Data + AI Study Buddy.

Run with:

    streamlit run app.py
"""

import streamlit as st

from llm_service import ChatService

st.set_page_config(
    page_title="Data + AI Study Buddy",
    page_icon="📚"
)

st.title("📚 Data + AI Study Buddy")

# --------------------------------------------------------------------------
# Sidebar
# --------------------------------------------------------------------------

with st.sidebar:
    st.header("Settings")

    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.5,
        value=0.4,
        step=0.1,
    )

    if st.button("Clear chat"):
        st.session_state.pop("service", None)
        st.session_state.pop("messages", None)
        st.rerun()

# --------------------------------------------------------------------------
# Session State
# --------------------------------------------------------------------------

if "service" not in st.session_state:
    st.session_state.service = ChatService(
        temperature=temperature
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

service: ChatService = st.session_state.service
service.temperature = temperature

# --------------------------------------------------------------------------
# Display previous messages
# --------------------------------------------------------------------------

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --------------------------------------------------------------------------
# User input
# --------------------------------------------------------------------------

if prompt := st.chat_input("Ask a Data or AI question..."):

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        reply = st.write_stream(service.stream(prompt))

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": reply,
        }
    )

# --------------------------------------------------------------------------
# Token usage
# --------------------------------------------------------------------------

with st.sidebar:
    st.markdown("---")
    st.caption(
        f"Input Tokens: {service.total_input_tokens}"
    )
    st.caption(
        f"Output Tokens: {service.total_output_tokens}"
    )