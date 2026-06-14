"""
Streamlit chat UI for ChefBot — Recipe & Meal-Planner Assistant.

Run with:
    pip install -r requirements.txt
    streamlit run app.py
"""

import streamlit as st
from llm_service import ChatService

st.set_page_config(page_title="ChefBot 🍳", page_icon="🍳", layout="centered")
st.title("🍳 ChefBot — Your Personal Meal Planner")
st.caption("Ask me about recipes, meal plans, dietary substitutions, and more!")

# ── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("⚙️ Settings")

    temperature = st.slider(
        "Creativity (temperature)",
        min_value=0.0,
        max_value=1.5,
        value=0.4,
        step=0.1,
        help="Lower = more consistent recipes. Higher = more creative suggestions.",
    )

    model_choice = st.selectbox(
        "Model",
        options=["gemini-2.0-flash", "gemini-1.5-flash"],
        index=0,
        help="gemini-2.0-flash is faster; gemini-1.5-flash is the fallback.",
    )

    st.divider()

    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.pop("service", None)
        st.session_state.pop("messages", None)
        st.rerun()

    st.divider()
    st.markdown("**💡 Try asking:**")
    st.markdown("- *What can I make with chicken, lemon, and garlic?*")
    st.markdown("- *Give me a 3-day vegan meal plan*")
    st.markdown("- *I'm allergic to nuts — suggest a pesto recipe*")
    st.markdown("- *How many calories in a bowl of lentil soup?*")

# ── Session state ─────────────────────────────────────────────────────────────

if "service" not in st.session_state:
    try:
        st.session_state.service = ChatService(
            model=model_choice, temperature=temperature
        )
    except EnvironmentError as e:
        st.error(str(e))
        st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

service: ChatService = st.session_state.service
service.temperature = temperature
service.model_name = model_choice

# ── Render history ────────────────────────────────────────────────────────────

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Handle new user turn ──────────────────────────────────────────────────────

if prompt := st.chat_input("What would you like to cook today?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        reply = st.write_stream(service.stream(prompt))

    st.session_state.messages.append({"role": "assistant", "content": reply})

# ── Token usage in sidebar ────────────────────────────────────────────────────

with st.sidebar:
    st.divider()
    st.caption("📊 **Token usage (this session)**")
    col1, col2 = st.columns(2)
    col1.metric("Input", service.total_input_tokens)
    col2.metric("Output", service.total_output_tokens)
