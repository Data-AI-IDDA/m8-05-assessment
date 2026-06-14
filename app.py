import streamlit as st

from llm_service import ChatService

st.set_page_config(page_title="StudyBuddy — AI/ML Assistant", page_icon="🤖")
st.title("🤖 StudyBuddy — Ironhack AI/ML Assistant")
st.caption("Ask me anything about machine learning, LLMs, prompt engineering, or course code!")

with st.sidebar:
    st.header("Settings")
    temperature = st.slider("Temperature", 0.0, 1.5, 0.4, 0.1,
                            help="Lower = more focused, Higher = more creative")
    if st.button("🗑️ Clear chat"):
        st.session_state.pop("service", None)
        st.session_state.pop("messages", None)
        st.rerun()
    st.markdown("---")
    st.markdown("**Topics I can help with:**")
    st.markdown("- LLMs & Prompt Engineering\n- Evaluation & Evals\n- Safety & Guardrails\n- ML Concepts\n- Python / ML Code")

if "service" not in st.session_state:
    st.session_state.service = ChatService(temperature=temperature)

if "messages" not in st.session_state:
    st.session_state.messages = []

service: ChatService = st.session_state.service
service.temperature = temperature

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask a question about AI/ML…"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        reply = st.write_stream(service.stream(prompt))

    st.session_state.messages.append({"role": "assistant", "content": reply})

with st.sidebar:
    st.markdown("---")
    st.caption(
        f"📊 Token usage\n\n"
        f"Input: **{service.total_input_tokens}**  \n"
        f"Output: **{service.total_output_tokens}**"
    )
