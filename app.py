"""
Streamlit chat UI for the LLM chat micro-service — "CourseAI Study Buddy".

Run with:

    pip install -r requirements.txt
    cp .env.example .env   # then add your GEMINI_API_KEY
    streamlit run app.py

Satisfies the frontend requirements:
  - chat interface using st.chat_message / st.chat_input
  - conversation history visible across turns
  - streaming responses (st.write_stream)
  - sidebar controls: temperature slider + "Clear chat" button
  - token usage shown so cost is visible
"""

import streamlit as st

from llm_service import ChatService

st.set_page_config(page_title="CourseAI Study Buddy", page_icon="📚")
st.title("📚 CourseAI Study Buddy")
st.caption("Your tutor for the LLM-engineering week — prompting, model choice, evaluation & safety.")

# --- Sidebar controls (Requirement: at least one small control) ------------
with st.sidebar:
    st.header("Settings")
    temperature = st.slider(
        "Temperature", 0.0, 1.5, 0.3, 0.1,
        help="Low = focused & consistent (good for a study tutor). High = more varied.",
    )
    if st.button("🧹 Clear chat", use_container_width=True):
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
if prompt := st.chat_input("Ask about prompting, model choice, eval, or safety…"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            reply = st.write_stream(service.stream(prompt))
        except Exception as e:  # surface config errors (e.g. missing API key) in-UI
            reply = f"⚠️ {e}"
            st.error(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})

# --- Cost visibility (Requirement: token usage tracked) --------------------
with st.sidebar:
    st.divider()
    st.subheader("Token usage")
    st.metric("Input tokens", service.total_input_tokens)
    st.metric("Output tokens", service.total_output_tokens)
    st.caption(f"Backend: `{service.backend}` · model: `{service.model}`")
