"""
Streamlit chat UI for the AI/ML/LLM Study Buddy.

Run with:
    pip install -r requirements.txt
    streamlit run app.py
"""

import streamlit as st
from llm_service import ChatService, DEFAULT_MODEL

st.set_page_config(
    page_title="StudyBuddy — AI/ML/LLM Tutor",
    page_icon="🎓",
    layout="centered",
)

st.title("🎓 StudyBuddy")
st.caption("Your personal AI/ML/LLM tutor. Ask me anything about the course!")

# --- Sidebar ---------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Settings")

    model = st.selectbox(
        "Model",
        ["llama3.2:3b", "qwen2.5:0.5b", "moondream:latest"],
        index=0,
        help="Choose your local Ollama model",
    )

    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.5,
        value=0.4,
        step=0.1,
        help="Lower = more focused answers. Higher = more creative.",
    )

    st.divider()

    st.markdown("**📚 Topic Suggestions**")
    topics = [
        "What is a transformer?",
        "Explain embeddings",
        "What is RAG?",
        "How does fine-tuning work?",
        "Quiz me on LLMs!",
        "What is prompt engineering?",
    ]
    for topic in topics:
        if st.button(topic, use_container_width=True):
            st.session_state["quick_prompt"] = topic

    st.divider()

    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.pop("service", None)
        st.session_state.pop("messages", None)
        st.rerun()

    st.divider()
    st.markdown("**📊 Token Usage**")

# --- State -----------------------------------------------------------------
if "service" not in st.session_state or st.session_state.get("model") != model:
    st.session_state.service = ChatService(model=model, temperature=temperature)
    st.session_state.model = model
    st.session_state.messages = []

if "messages" not in st.session_state:
    st.session_state.messages = []

service: ChatService = st.session_state.service
service.temperature = temperature

# --- Render history --------------------------------------------------------
if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.markdown(
            "👋 Hi! I'm **StudyBuddy**, your AI/ML/LLM tutor.\n\n"
            "I can help you:\n"
            "- 📖 **Explain** concepts (transformers, embeddings, RAG, fine-tuning...)\n"
            "- 🧠 **Quiz** you on any topic\n"
            "- 🔍 **Break down** complex ideas step by step\n\n"
            "What would you like to study today?"
        )

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Handle quick prompt from sidebar buttons ------------------------------
if "quick_prompt" in st.session_state:
    quick = st.session_state.pop("quick_prompt")
    st.session_state.messages.append({"role": "user", "content": quick})
    with st.chat_message("user"):
        st.markdown(quick)
    with st.chat_message("assistant"):
        reply = st.write_stream(service.stream(quick))
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()

# --- Handle new user input -------------------------------------------------
if prompt := st.chat_input("Ask me about AI, ML, or LLMs..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        reply = st.write_stream(service.stream(prompt))

    st.session_state.messages.append({"role": "assistant", "content": reply})

# --- Token usage in sidebar ------------------------------------------------
with st.sidebar:
    st.metric("Input tokens", service.total_input_tokens)
    st.metric("Output tokens", service.total_output_tokens)
    st.caption("Running on local Ollama — $0 cost 🎉")