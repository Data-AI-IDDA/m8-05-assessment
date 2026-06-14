"""
Streamlit chat UI — CodeLens: AI Code Explainer
Run with:
    pip install -r requirements.txt
    streamlit run app.py
"""

import streamlit as st
from llm_service import ChatService

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CodeLens — AI Code Explainer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Hide Streamlit default header */
    #MainMenu {visibility: hidden;}
    /* header {visibility: hidden;} */
    footer {visibility: hidden;}
    
    /* App background */
    .stApp { background-color: #0f1117; }

    /* Chat messages */
    .stChatMessage {
        border-radius: 12px;
        margin-bottom: 8px;
    }

    /* Code blocks inside chat */
    .stChatMessage code {
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
        font-size: 13px;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 12px;
    }

    /* Input box */
    .stChatInputContainer {
        border-top: 1px solid #30363d;
    }

    /* Follow-up buttons */
    .stButton > button {
        background-color: #161b22;
        border: 1px solid #30363d;
        color: #8b949e;
        border-radius: 6px;
        font-size: 12px;
        padding: 4px 12px;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        border-color: #58a6ff;
        color: #58a6ff;
        background-color: #1f2937;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 8])
with col_logo:
    st.markdown("## 🔍")
with col_title:
    st.markdown("## CodeLens")
    st.caption("Paste any code snippet — I'll explain it clearly, line by line.")

st.divider()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Settings")

    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.5,
        value=0.4,
        step=0.1,
        help="Lower = more focused and deterministic. Higher = more creative.",
    )

    explanation_level = st.radio(
        "Explanation level",
        options=["🟢 Beginner", "🟡 Intermediate", "🔴 Expert"],
        index=1,
        help="Controls how technical the explanation will be.",
    )

    st.divider()

    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.pop("service", None)
        st.session_state.pop("messages", None)
        st.rerun()

    st.divider()
    st.markdown("### 📊 Token Usage")

# ── Session state ──────────────────────────────────────────────────────────────
if "service" not in st.session_state:
    st.session_state.service = ChatService(temperature=temperature)

if "messages" not in st.session_state:
    st.session_state.messages = []

service: ChatService = st.session_state.service
service.temperature = temperature

# Inject explanation level into service system awareness via a note in history
# (We append it to the user message automatically below)
level_map = {
    "🟢 Beginner": "Explain as if I am a complete beginner. Use simple words and analogies.",
    "🟡 Intermediate": "Assume I know the basics. Be technically precise but clear.",
    "🔴 Expert": "I am an expert. Be concise, focus on non-obvious behaviour, edge cases, and performance.",
}
level_instruction = level_map[explanation_level]

# ── Render chat history ────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Follow-up shortcut buttons ────────────────────────────────────────────────
if st.session_state.messages:
    st.markdown("**Quick follow-ups:**")
    col1, col2, col3 = st.columns(3)
    followup_prompt = None
    with col1:
        if st.button("🐛 Find bugs"):
            followup_prompt = "Can you look for any bugs or logical errors in the code above?"
    with col2:
        if st.button("⚡ Optimize it"):
            followup_prompt = "How can this code be optimized for performance or readability?"
    with col3:
        if st.button("🧪 Write a test"):
            followup_prompt = "Can you write a simple unit test for the code above?"

    if followup_prompt:
        # Inject as if user typed it
        st.session_state._pending_prompt = followup_prompt
        st.rerun()

# ── Handle pending follow-up (from button click) ──────────────────────────────
pending = st.session_state.pop("_pending_prompt", None)

# ── Chat input ────────────────────────────────────────────────────────────────
user_input = st.chat_input("Paste your code here or ask a question…")
prompt = pending or user_input

if prompt:
    # Append level instruction to first user message or always (lightweight)
    enriched_prompt = f"{prompt}\n\n[Explanation level: {level_instruction}]"

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Safety warning BEFORE assistant reply
    danger_warning = service._check_dangerous_code(prompt)
    if danger_warning:
        st.warning(danger_warning)

    with st.chat_message("assistant"):
        reply = st.write_stream(service.stream(enriched_prompt))

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()

# ── Token metrics in sidebar ──────────────────────────────────────────────────
with st.sidebar:
    col_in, col_out = st.columns(2)
    with col_in:
        st.metric("Input tokens", f"{service.total_input_tokens:,}")
    with col_out:
        st.metric("Output tokens", f"{service.total_output_tokens:,}")

    total = service.total_input_tokens + service.total_output_tokens
    st.caption(f"Total: {total:,} tokens")

# ── Empty state ───────────────────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown("""
    <div style="text-align:center; padding: 60px 20px; color: #8b949e;">
        <div style="font-size: 48px;">🔍</div>
        <h3 style="color: #c9d1d9;">Paste any code snippet to get started</h3>
        <p>I can explain Python, JavaScript, SQL, Bash, and more.</p>
        <p style="font-size:12px;">Try pasting a function, a class, or even a tricky one-liner.</p>
    </div>
    """, unsafe_allow_html=True)
