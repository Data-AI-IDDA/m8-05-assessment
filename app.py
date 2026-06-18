"""
app.py — MealMate: a recipe & meal-planning Streamlit chat assistant.

Run with: streamlit run app.py
"""

import streamlit as st
from llm_service import ChatSession, MODEL_NAME

st.set_page_config(page_title="MealMate", page_icon="🍳", layout="centered")

# -----------------------------------------------------------------------
# Sidebar controls
# -----------------------------------------------------------------------
with st.sidebar:
    st.title("🍳 MealMate")
    st.caption("Your recipe & meal-planning assistant")

    temperature = st.slider(
        "Creativity (temperature)",
        min_value=0.0, max_value=1.0, value=0.7, step=0.1,
        help="Lower = more predictable recipes, higher = more creative suggestions.",
    )

    if st.button("🗑️ Clear chat"):
        st.session_state.pop("chat_session", None)
        st.session_state.pop("messages", None)
        st.rerun()

    st.divider()
    st.markdown(f"**Model:** `{MODEL_NAME}` (Ollama, local)")

    if "chat_session" in st.session_state:
        cs = st.session_state.chat_session
        st.markdown("**Token usage (session total)**")
        st.write(f"Input tokens: {cs.total_input_tokens}")
        st.write(f"Output tokens: {cs.total_output_tokens}")

# -----------------------------------------------------------------------
# Session state init
# -----------------------------------------------------------------------
if "chat_session" not in st.session_state:
    try:
        st.session_state.chat_session = ChatSession(temperature=temperature)
    except Exception as e:
        st.error(
            f"Could not start chat session: {e}\n\n"
            "Make sure Ollama is running locally (`ollama serve`) and that "
            f"the model `{MODEL_NAME}` has been pulled (`ollama pull {MODEL_NAME}`)."
        )
        st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

# -----------------------------------------------------------------------
# Render history
# -----------------------------------------------------------------------
st.title("🍳 MealMate")
st.caption("Ask for recipes, meal plans, or substitutions — tell me your dietary needs!")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -----------------------------------------------------------------------
# Chat input + streaming response
# -----------------------------------------------------------------------
if prompt := st.chat_input("e.g. 'Give me a vegetarian dinner for 2 under 30 minutes'"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            response_text = st.write_stream(
                st.session_state.chat_session.send_message_stream(prompt)
            )
        except Exception as e:
            response_text = f"⚠️ Error talking to Ollama: {e}"
            st.markdown(response_text)

    st.session_state.messages.append({"role": "assistant", "content": response_text})
    st.rerun()