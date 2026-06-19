"""
app.py
------
Streamlit chat UI for the "AI & ML Bootcamp Study Buddy".

Run with:
    streamlit run app.py

Requires a local Ollama server running with the target model pulled:
    ollama pull llama3.2:3b
    ollama serve   (usually already running as a background service)
"""

import streamlit as st

from llm_service import StudyBuddyService, DEFAULT_MODEL

st.set_page_config(page_title="Study Buddy", page_icon="📚", layout="centered")

# --------------------------------------------------------------------------
# Sidebar controls
# --------------------------------------------------------------------------

with st.sidebar:
    st.header("⚙️ Settings")

    model_choice = st.selectbox(
        "Ollama model",
        options=["llama3.2:3b", "llama3.2:1b", "qwen2.5:3b", "phi3:mini"],
        index=0,
        help="Must already be pulled locally via `ollama pull <model>`.",
    )

    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.4,
        step=0.05,
        help="Lower = more focused/deterministic answers. Higher = more varied.",
    )

    st.divider()

    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.pop("service", None)
        st.session_state.pop("display_history", None)
        st.rerun()

    st.divider()
    st.subheader("📊 Token usage (this session)")
    usage_placeholder = st.empty()

    st.divider()
    st.caption(
        "Study Buddy answers questions about this bootcamp's material only: "
        "Python, LLM prompting, model choice, evaluation, and AI safety. "
        "It will politely decline anything outside that scope, and it "
        "ignores instructions embedded in pasted text."
    )

# --------------------------------------------------------------------------
# Session state: one StudyBuddyService instance per browser session
# --------------------------------------------------------------------------

needs_new_service = (
    "service" not in st.session_state
    or st.session_state.service.model != model_choice
    or st.session_state.service.options.get("temperature") != temperature
)

if needs_new_service:
    st.session_state.service = StudyBuddyService(
        model=model_choice,
        options={"temperature": temperature},
    )
    st.session_state.display_history = []

service: StudyBuddyService = st.session_state.service

# --------------------------------------------------------------------------
# Main chat area
# --------------------------------------------------------------------------

st.title("📚 Study Buddy")
st.caption(
    "Your focused assistant for this AI/ML bootcamp — ask about Python, "
    "prompting, model choice, evaluation, or safety/guardrails."
)

# Render prior turns
for turn in st.session_state.display_history:
    with st.chat_message(turn["role"]):
        st.markdown(turn["content"])
        if turn["role"] == "assistant" and turn.get("badge"):
            st.caption(turn["badge"])

user_input = st.chat_input("Ask Study Buddy something about the course...")

if user_input:
    st.session_state.display_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        stream_box = st.empty()
        full_text = ""
        for chunk in service.send_stream(user_input):
            full_text += chunk
            stream_box.markdown(full_text + "▌")
        stream_box.markdown(full_text)

        meta = getattr(service, "last_call_meta", {})
        badge = None
        if meta.get("blocked"):
            badge = f"🛑 guardrail triggered ({meta.get('block_reason')})"
        else:
            u = meta.get("usage", {})
            badge = (
                f"🔢 prompt={u.get('prompt_tokens', 0)} · "
                f"completion={u.get('completion_tokens', 0)} · "
                f"session_total={service.usage.total_tokens}"
            )
        st.caption(badge)

    st.session_state.display_history.append(
        {"role": "assistant", "content": full_text, "badge": badge}
    )

# --------------------------------------------------------------------------
# Sidebar usage table (rendered after any call so it's up to date)
# --------------------------------------------------------------------------

with usage_placeholder.container():
    st.metric("Total tokens", service.usage.total_tokens)
    st.metric("Calls made", service.usage.call_count)
    if service.usage.history:
        st.dataframe(service.usage.history, use_container_width=True, hide_index=True)
