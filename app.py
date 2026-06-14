"""
Streamlit chat UI for the LLM chat micro-service.
"""

import streamlit as st
from llm_service import ChatService

st.set_page_config(
    page_title="AI/ML Study Buddy",
    page_icon="📚",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom premium styling using CSS
st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #4B5563;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
    }
    /* Token usage card styling */
    .token-card {
        background-color: #F3F4F6;
        padding: 10px;
        border-radius: 8px;
        border-left: 5px solid #3B82F6;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">📚 AI/ML Study Buddy</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Your friendly AI companion to learn Machine Learning, Prompting, Evaluation, and Safety!</div>', unsafe_allow_html=True)

# Sidebar Configuration
st.sidebar.title("🛠️ Configuration")

# Model Selection
model_option = st.sidebar.selectbox(
    "Choose Model",
    ["gemini-flash-latest", "gemini-2.0-flash", "gemini-2.5-flash", "gemini-3.5-flash"],
    index=0,
    help="Gemini Flash Latest is recommended for free tier usage."
)

# Temperature Slider
temp_option = st.sidebar.slider(
    "Temperature",
    min_value=0.0,
    max_value=1.5,
    value=0.7,
    step=0.1,
    help="Higher values make output more creative, lower values make it more deterministic."
)

st.sidebar.markdown("---")

# Session state initialization for Chat Service
if "service" not in st.session_state or \
   st.session_state.current_model != model_option or \
   st.session_state.current_temp != temp_option:
    
    # Keep history if we are just tweaking parameters
    prev_history = st.session_state.service.history if "service" in st.session_state else []
    prev_in = st.session_state.service.total_input_tokens if "service" in st.session_state else 0
    prev_out = st.session_state.service.total_output_tokens if "service" in st.session_state else 0

    st.session_state.service = ChatService(model=model_option, temperature=temp_option)
    st.session_state.service.history = prev_history
    st.session_state.service.total_input_tokens = prev_in
    st.session_state.service.total_output_tokens = prev_out
    
    st.session_state.current_model = model_option
    st.session_state.current_temp = temp_option

if "messages" not in st.session_state:
    st.session_state.messages = []

service: ChatService = st.session_state.service

# Token usage display
st.sidebar.markdown("### 📊 Session Statistics")
st.sidebar.markdown(f"""
<div class="token-card">
    <strong>Input Tokens:</strong> {service.total_input_tokens}<br/>
    <strong>Output Tokens:</strong> {service.total_output_tokens}<br/>
    <strong>Total Tokens:</strong> {service.total_input_tokens + service.total_output_tokens}
</div>
""", unsafe_allow_html=True)

# Estimated cost calculation (Based on Gemini 1.5 Flash pricing: $0.075 / 1M input, $0.30 / 1M output tokens)
cost = (service.total_input_tokens * 0.075 / 1_000_000) + \
       (service.total_output_tokens * 0.30 / 1_000_000)
st.sidebar.caption(f"Estimated Session Cost: ${cost:.6f} USD")

# Clear chat button
if st.sidebar.button("🗑️ Clear Conversation History", type="secondary"):
    service.reset()
    st.session_state.messages = []
    st.rerun()

# Welcome message if chat history is empty
if len(st.session_state.messages) == 0:
    with st.chat_message("assistant"):
        st.write("Hello! I am your AI/ML Study Buddy. Let's learn together! Ask me anything about machine learning, prompting, evaluation, or security. Or type **'Quiz me'** to test your knowledge!")

# Render existing chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Accept user input
if prompt := st.chat_input("What is prompt injection?"):
    # Append and render user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get generator for response and stream it
    with st.chat_message("assistant"):
        reply = st.write_stream(service.stream(prompt))
    
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()
