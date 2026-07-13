import streamlit as st
from llm_service import ChatService

st.set_page_config(page_title="PyMentor Chat", page_icon="🐍")
st.title("🐍 PyMentor: Code Review & Explainer")
st.caption("Paste your Python code below for an explanation, bug check, or refactor.")

# --- Sidebar control ---
with st.sidebar:
    st.header("Settings")
    temperature = st.slider("Temperature", 0.0, 1.0, 0.2, 0.1, help="Lower values mean more deterministic code outputs.")
    
    if st.button("Clear chat"):
        st.session_state.pop("service", None)
        st.session_state.pop("messages", None)
        st.rerun()

# --- State ---
if "service" not in st.session_state:
    st.session_state.service = ChatService(temperature=temperature)
if "messages" not in st.session_state:
    st.session_state.messages = []

service: ChatService = st.session_state.service
service.temperature = temperature

# --- Render history ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Handle a new user turn ---
if prompt := st.chat_input("Paste your Python code or ask a question…"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Streaming the generator from the backend service
        reply = st.write_stream(service.stream(prompt))

    st.session_state.messages.append({"role": "assistant", "content": reply})

# --- Cost visibility ---
with st.sidebar:
    st.divider()
    st.caption("📊 **Session Token Usage**")
    st.caption(f"**Input (Prompt):** {service.total_input_tokens}")
    st.caption(f"**Output (Generated):** {service.total_output_tokens}")