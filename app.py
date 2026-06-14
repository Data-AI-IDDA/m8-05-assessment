"""
Streamlit chat UI for the LLM chat micro-service.

Run with:

    pip install -r requirements.txt
    streamlit run app.py

Requirements satisfied:
  - a chat interface using st.chat_message / st.chat_input
  - conversation history visible across turns
  - streaming responses
  - one small control (model / temperature picker + "clear chat")
"""

import streamlit as st

from llm_service import ChatService

st.set_page_config(page_title="ChefAI - Recipe & Meal Planner", page_icon="🍳")
st.title("🍳 ChefAI: Recipe & Meal-Planner Assistant")

# --- Sidebar control (Requirement: one small control) ----------------------
with st.sidebar:
    st.header("Settings")
    temperature = st.slider("Temperature", 0.0, 1.5, 0.3, 0.1)

    model_choice = st.selectbox(
        "Model",
        ["gemini-2.5-flash"],
        help="Gemini 2.5 Flash is selected for ultra-low latency and balanced reasoning."
    )

    if st.button("Clear chat"):
        st.session_state.pop("service", None)
        st.session_state.pop("messages", None)
        st.rerun()

# --- State -----------------------------------------------------------------
if "service" not in st.session_state:
    st.session_state.service = ChatService(model=model_choice, temperature=temperature)
if "messages" not in st.session_state:
    st.session_state.messages = []

service: ChatService = st.session_state.service
service.temperature = temperature
service.model = model_choice

# --- Render history --------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Handle a new user turn ------------------------------------------------
if prompt := st.chat_input("Ask me about recipes, meal plans, or dietary adjustments…"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        reply = st.write_stream(service.stream(prompt))

    st.session_state.messages.append({"role": "assistant", "content": reply})

# --- Cost visibility (Requirement: token usage tracked) --------------------
with st.sidebar:
    st.markdown("---")
    st.subheader("📊 Metrics & Usage")
    st.caption(
        f"Tokens — in: {service.total_input_tokens} / "
        f"out: {service.total_output_tokens}"
    )

    # Approximate cost based on Gemini 2.5 Flash pricing (per 1M tokens)
    estimated_cost = (service.total_input_tokens * 0.075 / 1_000_000) + \
                     (service.total_output_tokens * 0.30 / 1_000_000)
    st.caption(f"Estimated Cost: ${estimated_cost:.6f}")