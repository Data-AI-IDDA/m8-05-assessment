import streamlit as st
from llm_service import ChatService

st.set_page_config(page_title="StudyBot — AI Study Buddy", page_icon="🤖")
st.title("🤖 StudyBot — AI Study Buddy")
st.caption("Your study buddy for LLMs & applied AI — ask anything from the course.")

# --- Sidebar controls -------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Settings")

    temperature = st.slider("Temperature", 0.0, 1.5, 0.4, 0.1)

    model_choice = st.selectbox(
        "Model",
        options=["llama3.2", "llama3.1", "mistral"],
        index=0,
    )

    quiz_mode = st.toggle("Quiz mode 🎓", value=False)

    st.divider()

    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.pop("service", None)
        st.session_state.pop("messages", None)
        st.rerun()

# --- State ------------------------------------------------------------------
if "service" not in st.session_state:
    st.session_state.service = ChatService(model=model_choice, temperature=temperature)
if "messages" not in st.session_state:
    st.session_state.messages = []

service: ChatService = st.session_state.service
service.temperature = temperature

# --- Render history ---------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Welcome message if chat is empty ---------------------------------------
if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.markdown(
            "👋 Hi! I'm **StudyBot**, your study buddy for this AI/LLM course.\n\n"
            "I can help you with:\n"
            "- 📖 Explaining concepts (prompting, RAG, evals, safety, fine-tuning…)\n"
            "- 🧪 Quizzing you on course material\n"
            "- 💡 Giving examples and analogies\n\n"
            "What would you like to study today?"
        )

# --- Handle new user turn ---------------------------------------------------
if prompt := st.chat_input("Ask me anything about AI & LLMs…"):
    effective_prompt = (
        prompt + "\n\n[After answering, ask me one short quiz question on this topic.]"
        if quiz_mode
        else prompt
    )

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        reply = st.write_stream(service.stream(effective_prompt))

    st.session_state.messages.append({"role": "assistant", "content": reply})

# --- Token usage in sidebar -------------------------------------------------
with st.sidebar:
    st.divider()
    st.caption(
        f"📊 Tokens — in: {service.total_input_tokens:,} / "
        f"out: {service.total_output_tokens:,}"
    ) 