"""
Streamlit chat UI for the Support Triage micro-service.

Run with:
    streamlit run app.py
"""

import streamlit as st

from llm_service import ChatService

st.set_page_config(page_title="Support Triage Assistant", page_icon="🎫")
st.title("🎫 Support Triage Assistant")
st.caption("Describe your issue and I'll classify and route it for you.")

# ---------------------------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Settings")

    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.2,
        step=0.1,
        help="Lower = more consistent triage; higher = more varied phrasing.",
    )

    st.divider()

    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.pop("service", None)
        st.session_state.pop("messages", None)
        st.rerun()

    st.divider()
    st.markdown("**Token usage (this session)**")
    token_placeholder = st.empty()

# ---------------------------------------------------------------------------
# Session state — one ChatService instance persists across Streamlit reruns
# ---------------------------------------------------------------------------
if "service" not in st.session_state:
    st.session_state.service = ChatService(temperature=temperature)
if "messages" not in st.session_state:
    st.session_state.messages = []

service: ChatService = st.session_state.service
service.temperature = temperature  # respect slider changes mid-session

# ---------------------------------------------------------------------------
# Render existing conversation history
# ---------------------------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------------------------------------------------------------------
# Handle a new user turn
# ---------------------------------------------------------------------------
if prompt := st.chat_input("Describe your support issue…"):
    # Show the user bubble immediately
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Stream the assistant reply
    with st.chat_message("assistant"):
        reply = st.write_stream(service.stream(prompt))

    st.session_state.messages.append({"role": "assistant", "content": reply})

# ---------------------------------------------------------------------------
# Update token counter in sidebar (runs after every rerun)
# ---------------------------------------------------------------------------
token_placeholder.caption(
    f"Input tokens: {service.total_input_tokens}\n\n"
    f"Output tokens: {service.total_output_tokens}"
)