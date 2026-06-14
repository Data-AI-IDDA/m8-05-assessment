"""
Streamlit chat UI — StudyBot: AI/Data Science Study Buddy.

Run with:
    pip install -r requirements.txt
    streamlit run app.py
"""

import streamlit as st

from llm_service import ChatService

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="StudyBot — AI/DS Study Buddy",
    page_icon="🎓",
    layout="centered",
)
st.title("🎓 StudyBot — AI/Data Science Study Buddy")
st.caption(
    "Ask me anything about ML, AI, Python, or statistics.  "
    "I can also **quiz you** on any topic!"
)

# ── Sidebar controls ───────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")

    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.5,
        value=0.4,
        step=0.1,
        help="Lower = more precise/factual · Higher = more creative/varied",
    )

    model = st.selectbox(
        "Model",
        options=["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"],
        index=0,
        help=(
            "gemini-2.0-flash — fastest, free-tier friendly (recommended)\n"
            "gemini-1.5-pro — more capable but slower"
        ),
    )

    st.divider()

    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.pop("service", None)
        st.session_state.pop("messages", None)
        st.rerun()

    # ── Quick starters ─────────────────────────────────────────────────────
    st.divider()
    st.caption("**💡 Quick starters**")
    STARTERS = [
        "Explain gradient descent with an analogy",
        "Quiz me on neural networks",
        "What is the bias-variance trade-off?",
        "Walk me through k-fold cross-validation",
        "What's the difference between precision and recall?",
        "Explain backpropagation step by step",
    ]
    for s in STARTERS:
        if st.button(s, use_container_width=True, key=f"starter_{s}"):
            st.session_state["_starter"] = s
            st.rerun()

# ── Session state ──────────────────────────────────────────────────────────────
if "service" not in st.session_state:
    try:
        st.session_state.service = ChatService(model=model, temperature=temperature)
    except EnvironmentError as e:
        st.error(str(e))
        st.info(
            "**Quick fix:**\n"
            "1. Copy `.env.example` → `.env`\n"
            "2. Paste your key from https://aistudio.google.com\n"
            "3. Restart `streamlit run app.py`"
        )
        st.stop()

if "messages" not in st.session_state:
    st.session_state.messages: list[dict[str, str]] = []

service: ChatService = st.session_state.service

# Live-update sampling settings without restarting
service.temperature = temperature
service.model = model

# ── Render conversation history ────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Handle sidebar quick-starter button ───────────────────────────────────────
starter_prompt: str | None = st.session_state.pop("_starter", None)

# ── Handle new user input ──────────────────────────────────────────────────────
prompt: str | None = st.chat_input("Ask about ML, AI, Python, statistics…") or starter_prompt

if prompt:
    # Display the user's message immediately
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Stream the assistant's reply
    with st.chat_message("assistant"):
        # st.write_stream consumes the generator, displays chunks live,
        # and returns the concatenated string.
        reply: str = st.write_stream(service.stream(prompt))

    # Store for history display on next rerun
    st.session_state.messages.append({"role": "assistant", "content": reply})

# ── Token usage footer (updates after each turn) ──────────────────────────────
with st.sidebar:
    st.divider()
    col1, col2 = st.columns(2)
    col1.metric("Tokens in", f"{service.total_input_tokens:,}")
    col2.metric("Tokens out", f"{service.total_output_tokens:,}")
    st.caption("Token counts reset when you clear chat.")
