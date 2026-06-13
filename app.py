"""
app.py — StudyBuddy Streamlit UI
Handles the chat interface, sidebar controls, streaming display,
and persistent multi-session chat history.
"""

import streamlit as st
import json
import os
import time
from llm_service import LLMService
from safety.guardrail import check_input_safety

# ─────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────
HISTORY_DIR = "chat_histories"
os.makedirs(HISTORY_DIR, exist_ok=True)


# ─────────────────────────────────────────────────────
# Session persistence helpers
# ─────────────────────────────────────────────────────
def list_sessions() -> list[str]:
    """Return saved session filenames sorted newest first."""
    files = [f for f in os.listdir(HISTORY_DIR) if f.endswith(".json")]
    files.sort(reverse=True)
    return files


def load_session(filename: str) -> list[dict]:
    with open(os.path.join(HISTORY_DIR, filename)) as f:
        return json.load(f)


def save_session(filename: str, messages: list[dict]) -> None:
    with open(os.path.join(HISTORY_DIR, filename), "w") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)


def new_session_name() -> str:
    return f"chat_{time.strftime('%Y%m%d_%H%M%S')}.json"


def session_label(filename: str) -> str:
    """Human-readable label from filename."""
    # chat_20260613_213045.json → 2026-06-13 21:30
    name = filename.replace("chat_", "").replace(".json", "")
    try:
        dt = time.strptime(name, "%Y%m%d_%H%M%S")
        return time.strftime("%Y-%m-%d %H:%M", dt)
    except Exception:
        return filename


# ─────────────────────────────────────────────────────
# Page configuration
# ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="StudyBuddy — AI/ML Assistant",
    page_icon="🤖",
    layout="centered",
)

# ─────────────────────────────────────────────────────
# Session state defaults
# ─────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_session" not in st.session_state:
    st.session_state.current_session = new_session_name()

# ─────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Settings")
    st.markdown("---")

    model_choice = st.selectbox(
        label="Model",
        options=["llama3.2", "llama3.1", "mistral", "codellama", "phi3"],
        index=0,
        help="Select any model you have pulled via `ollama pull <model>`",
    )

    temperature = st.slider(
        label="Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.05,
        help="Lower = more deterministic. Higher = more creative.",
    )

    st.markdown("---")

    # ── New chat button ──────────────────────────────
    if st.button("✏️ New Chat", use_container_width=True, type="primary"):
        # Köhnə söhbəti saxla
        if st.session_state.messages:
            save_session(
                st.session_state.current_session,
                st.session_state.messages,
            )
        # Yeni sessiya başlat
        st.session_state.messages = []
        st.session_state.current_session = new_session_name()
        if "llm" in st.session_state:
            del st.session_state["llm"]
        st.rerun()

    if st.button("🗑️ Clear Chat", use_container_width=True):
        # Cari sessiyanı sil
        path = os.path.join(HISTORY_DIR, st.session_state.current_session)
        if os.path.exists(path):
            os.remove(path)
        st.session_state.messages = []
        st.session_state.current_session = new_session_name()
        if "llm" in st.session_state:
            del st.session_state["llm"]
        st.rerun()

    st.markdown("---")

    # ── Past sessions ────────────────────────────────
    sessions = list_sessions()
    if sessions:
        st.markdown("**💬 Chat History**")
        for filename in sessions:
            label = session_label(filename)
            # Cari sessiyanı highlight et
            is_current = filename == st.session_state.current_session
            btn_label = f"{'▶ ' if is_current else ''}{label}"
            if st.button(btn_label, use_container_width=True, key=f"sess_{filename}"):
                # Cari söhbəti saxla
                if st.session_state.messages:
                    save_session(
                        st.session_state.current_session,
                        st.session_state.messages,
                    )
                # Seçilən sessiyanı yüklə
                st.session_state.messages = load_session(filename)
                st.session_state.current_session = filename
                if "llm" in st.session_state:
                    del st.session_state["llm"]
                st.rerun()

    st.markdown("---")
    st.markdown("**🤖 StudyBuddy**")
    st.caption("AI/ML course assistant")
    st.caption("Powered by Ollama (local)")

    # Token usage
    if "llm" in st.session_state:
        stats = st.session_state.llm.get_token_stats()
        if stats["total_tokens"] > 0:
            st.markdown("---")
            st.markdown("**📊 Token Usage**")
            st.caption(f"Input:  {stats['total_input_tokens']:,}")
            st.caption(f"Output: {stats['total_output_tokens']:,}")
            st.caption(f"Total:  {stats['total_tokens']:,}")

# ─────────────────────────────────────────────────────
# LLM service init
# ─────────────────────────────────────────────────────
if "llm" not in st.session_state:
    st.session_state.llm = LLMService(
        model_name=model_choice,
        temperature=temperature,
    )

# ─────────────────────────────────────────────────────
# Page header
# ─────────────────────────────────────────────────────
st.title("🤖 StudyBuddy — AI/ML Course Assistant")
st.caption("Ask me anything from your ML/AI curriculum!")
st.markdown("---")

# ─────────────────────────────────────────────────────
# Render conversation history
# ─────────────────────────────────────────────────────
if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.markdown(
            "👋 Hello! I'm **StudyBuddy** — your AI/ML study companion.\n\n"
            "I can help you with:\n"
            "- 🧠 Explaining LLMs, RAG, and tokenization\n"
            "- 🏗️ Walking through model architectures (Transformers, CNNs, RNNs)\n"
            "- ⚙️ MLOps concepts — training pipelines, deployment, monitoring\n"
            "- 🔬 Fine-tuning, embeddings, and evaluation metrics\n"
            "- 📝 Quizzing you on course material\n\n"
            "What AI/ML topic shall we tackle today?"
        )

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ─────────────────────────────────────────────────────
# Chat input
# ─────────────────────────────────────────────────────
if prompt := st.chat_input("Ask me anything about AI/ML..."):

    # Safety check
    safety_result = check_input_safety(prompt)

    if not safety_result["safe"]:
        with st.chat_message("user"):
            st.markdown(prompt)

        warning = (
            f"⚠️ **Your message was flagged:** {safety_result['reason']}\n\n"
            "I'm StudyBuddy — I only help with AI/ML topics. "
            "Please ask a question from your AI/ML curriculum!"
        )
        with st.chat_message("assistant"):
            st.markdown(warning)

        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.messages.append({"role": "assistant", "content": warning})
        save_session(st.session_state.current_session, st.session_state.messages)
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""

        for chunk in st.session_state.llm.stream_response(
            user_message=prompt,
            history=st.session_state.messages[:-1],
        ):
            full_response += chunk
            placeholder.markdown(full_response + "▌")

        placeholder.markdown(full_response)

    st.session_state.messages.append(
        {"role": "assistant", "content": full_response}
    )

    
    save_session(st.session_state.current_session, st.session_state.messages)

    st.rerun()