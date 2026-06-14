"""
Streamlit chat UI for the LLM chat micro-service.

Run with:

    pip install -r requirements.txt
    streamlit run app.py

Requirements this file satisfies (see README):
  - a chat interface using st.chat_message / st.chat_input
  - conversation history visible across turns
  - streaming responses
  - small controls (model picker + temperature + "clear chat")
"""

import streamlit as st

from llm_service import ChatService

st.set_page_config(page_title="MealPlanner", page_icon="🍳")
st.title("🍳 MealPlanner — Recipe & Meal-Planning Assistant")

# --- Sidebar controls -------------------------------------------------------
with st.sidebar:
    st.header("Settings")
    temperature = st.slider("Temperature", 0.0, 1.5, 0.7, 0.1)
    model = st.text_input("Ollama model", value="llama3.2")

    if st.button("Clear chat"):
        st.session_state.pop("service", None)
        st.session_state.pop("messages", None)
        st.rerun()

# --- State -------------------------------------------------------------------
if "service" not in st.session_state:
    st.session_state.service = ChatService(model=model, temperature=temperature)
if "messages" not in st.session_state:
    st.session_state.messages = []

service: ChatService = st.session_state.service
service.temperature = temperature
service.model = model
service.options["temperature"] = temperature

# --- Render history ------------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Handle a new user turn -----------------------------------------------------
if prompt := st.chat_input("Type a message…"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # service.stream() yields text chunks from Ollama as they arrive.
        reply = st.write_stream(service.stream(prompt))

    st.session_state.messages.append({"role": "assistant", "content": reply})

# --- Cost visibility (Requirement: token usage tracked) -------------------------
with st.sidebar:
    st.caption(
        f"Tokens — in: {service.total_input_tokens} / "
        f"out: {service.total_output_tokens}"
    )