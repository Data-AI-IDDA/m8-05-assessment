"""
Streamlit chat UI — DataBuddy: DS/ML Study Assistant.

Run with:
    streamlit run app.py
"""

import streamlit as st

from llm_service import ChatService

st.set_page_config(page_title="DataBuddy — DS Study Assistant", page_icon="🤖")
st.title("🤖 DataBuddy — DS / ML Study Assistant")
st.caption("Ask me anything from the Ironhack ML & AI curriculum.")

# ---------------------------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Settings")

    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.5,
        value=0.4,
        step=0.1,
        help="Lower = more focused answers. Higher = more creative/varied.",
    )

    mode = st.radio(
        "Mode",
        options=["💬 Chat", "🎯 Quiz me!"],
        help="Quiz mode primes DataBuddy to ask you a question first.",
    )

    st.divider()

    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.pop("service", None)
        st.session_state.pop("messages", None)
        st.rerun()

    st.divider()
    st.markdown("**Model:** `minimax-m3:cloud` via Ollama")
    st.markdown("**Backend:** OpenAI-compatible local endpoint")

# ---------------------------------------------------------------------------
# Session state — one ChatService per session
# ---------------------------------------------------------------------------
if "service" not in st.session_state:
    st.session_state.service = ChatService(temperature=temperature)
if "messages" not in st.session_state:
    st.session_state.messages = []
if "mode_primed" not in st.session_state:
    st.session_state.mode_primed = None

service: ChatService = st.session_state.service
service.temperature = temperature  # live update from slider

# ---------------------------------------------------------------------------
# Quiz-mode primer: inject a first assistant message asking a question
# ---------------------------------------------------------------------------
if mode == "🎯 Quiz me!" and st.session_state.mode_primed != "quiz":
    st.session_state.messages = []
    service.reset()
    primer = (
        "Great! I'll quiz you on DS/ML topics. Here's your first question:\n\n"
        "**What is the difference between bias and variance in a machine learning "
        "model, and how do they contribute to model error?**"
    )
    st.session_state.messages.append({"role": "assistant", "content": primer})
    service.history.append({"role": "assistant", "content": primer})
    st.session_state.mode_primed = "quiz"
elif mode == "💬 Chat" and st.session_state.mode_primed != "chat":
    st.session_state.messages = []
    service.reset()
    st.session_state.mode_primed = "chat"

# ---------------------------------------------------------------------------
# Render conversation history
# ---------------------------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------------------------------------------------------------------
# Handle a new user turn
# ---------------------------------------------------------------------------
placeholder = (
    "Answer the question above…" if mode == "🎯 Quiz me!" else "Ask me anything DS/ML…"
)

if prompt := st.chat_input(placeholder):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        reply = st.write_stream(service.stream(prompt))

    st.session_state.messages.append({"role": "assistant", "content": reply})

# ---------------------------------------------------------------------------
# Token usage in sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.divider()
    st.caption("**Token usage (this session)**")
    st.caption(
        f"↑ In: {service.total_input_tokens:,}  |  "
        f"↓ Out: {service.total_output_tokens:,}"
    )
