"""
Streamlit UI for CourseAI Study Buddy.

    pip install -r requirements.txt
    cp .env.example .env   # add your GEMINI_API_KEY, or point at Ollama instead
    streamlit run app.py

Kept this file dumb on purpose — all the model/state/safety logic lives in
llm_service.py, this just renders it and reads the sidebar controls.
"""

import streamlit as st

from llm_service import ChatService

st.set_page_config(page_title="CourseAI Study Buddy", page_icon="📚")
st.title("📚 CourseAI Study Buddy")
st.caption("Your tutor for the LLM-engineering week — prompting, model choice, evaluation & safety.")

# --- Sidebar: temperature + clear chat --------------------------------
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

# --- Replay history on every rerun (Streamlit reruns the script top-to-bottom) ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- New turn ---------------------------------------------------------------
if prompt := st.chat_input("Ask about prompting, model choice, eval, or safety…"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            reply = st.write_stream(service.stream(prompt))
        except Exception as e:  # most likely a missing API key — show it, don't crash
            reply = f"⚠️ {e}"
            st.error(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})

# --- token counters live in the sidebar so cost is always visible ----------
with st.sidebar:
    st.divider()
    st.subheader("Token usage")
    st.metric("Input tokens", service.total_input_tokens)
    st.metric("Output tokens", service.total_output_tokens)
    st.caption(f"Backend: `{service.backend}` · model: `{service.model}`")
