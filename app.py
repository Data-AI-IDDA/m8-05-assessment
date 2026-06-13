import streamlit as st
from llm_service import chat_stream, get_usage
from safety.guardrail import is_safe

# --- Page setup ---
st.set_page_config(page_title="Recipe Assistant", page_icon="🍽️")
st.title("🍽️ Recipe & Meal-Planner Assistant")
st.caption("Ask me for recipes, meal plans, or cooking tips!")

# --- Sidebar ---
with st.sidebar:
    st.header("Settings")
    st.write("**Model:** llama3.2 (local Ollama)")

    if st.button("🗑️ Clear chat"):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.write("**Token usage this session:**")
    usage = get_usage()
    st.metric("Prompt tokens", usage["prompt"])
    st.metric("Completion tokens", usage["completion"])

    st.divider()
    st.write("**Try asking:**")
    st.write("- Simple pasta recipe?")
    st.write("- 5-day vegan meal plan")
    st.write("- Substitute for eggs in baking?")

# --- Initialize chat history ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Show existing messages ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Handle new user input ---
if prompt := st.chat_input("Ask about recipes or meal planning..."):

    # Safety check first
    if not is_safe(prompt):
        with st.chat_message("assistant"):
            st.warning(
                "⚠️ I can only help with food, recipes, and meal planning. "
                "Please ask a cooking-related question!"
            )
        st.stop()

    # Show user message
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Stream the assistant reply
    with st.chat_message("assistant"):
        full_reply = ""
        box = st.empty()

        for chunk in chat_stream(st.session_state.messages):
            full_reply += chunk
            box.markdown(full_reply + "▌")

        box.markdown(full_reply)

    # Save assistant reply to history
    st.session_state.messages.append({"role": "assistant", "content": full_reply})

    # Refresh sidebar token counter
    st.rerun()
