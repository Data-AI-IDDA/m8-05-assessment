"""
CodeLens — AI Code Explainer
Premium light-blue UI.
Run:  streamlit run app.py
"""

import streamlit as st
from llm_service import ChatService

st.set_page_config(
    page_title="CodeLens — AI Code Explainer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

/* ═══════ BASE ═══════ */
.main .block-container {
    background: transparent !important;
    max-width: 900px !important;
    margin: 0 auto !important;
    padding: 1.5rem 2rem 8rem !important;
}




/* ═══════ SIDEBAR ═══════ */
section[data-testid="stSidebar"] > div:first-child {
    padding: 1.25rem 1rem !important;
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label {
    color: #475569 !important;
    font-family: 'Inter', sans-serif !important;
}
section[data-testid="stSidebar"] [data-testid] {
    color: #334155 !important;
}

/* Sidebar selectbox */
section[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div {
    background: #F8FAFC !important;
    border: 1.5px solid #E2E8F0 !important;
    border-radius: 10px !important;
    color: #0F172A !important;
    font-size: 0.88rem !important;
    transition: border-color 0.2s !important;
}
section[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div:hover {
    border-color: #3B82F6 !important;
}

/* Sidebar slider */
[data-testid="stSlider"] [role="slider"] {
    background: #3B82F6 !important;
    border: 3px solid #FFFFFF !important;
    box-shadow: 0 0 0 3px #BFDBFE !important;
    width: 18px !important;
    height: 18px !important;
}

/* Sidebar buttons */
section[data-testid="stSidebar"] .stButton > button {
    background: #FFFFFF !important;
    color: #475569 !important;
    border: 1.5px solid #E2E8F0 !important;
    border-radius: 10px !important;
    font-size: 0.84rem !important;
    font-weight: 500 !important;
    width: 100% !important;
    padding: 0.5rem 0.8rem !important;
    transition: all 0.18s ease !important;
    font-family: 'Inter', sans-serif !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: #EFF6FF !important;
    border-color: #3B82F6 !important;
    color: #2563EB !important;
}

/* ═══════ CHAT MESSAGES ═══════ */
[data-testid="stChatMessage"] {
    border-radius: 16px !important;
    padding: 1.1rem 1.4rem !important;
    margin-bottom: 12px !important;
    animation: fadeUp 0.2s ease-out !important;
}
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* User — light blue */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background: #EFF6FF !important;
    border: 1px solid #BFDBFE !important;
    box-shadow: 0 1px 4px rgba(59,130,246,0.06) !important;
}

/* Assistant — white */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    box-shadow: 0 1px 6px rgba(0,0,0,0.04) !important;
}

/* Text */
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] li {
    color: #1E293B !important;
    font-size: 0.93rem !important;
    line-height: 1.8 !important;
}
[data-testid="stChatMessage"] h1,
[data-testid="stChatMessage"] h2,
[data-testid="stChatMessage"] h3 {
    color: #1D4ED8 !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    margin: 1rem 0 0.3rem !important;
}
[data-testid="stChatMessage"] strong { color: #0F172A !important; font-weight: 600 !important; }

/* Inline code */
[data-testid="stChatMessage"] code {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.82em !important;
    background: #EFF6FF !important;
    color: #1D4ED8 !important;
    border: 1px solid #BFDBFE !important;
    border-radius: 6px !important;
    padding: 2px 7px !important;
}

/* Code blocks */
[data-testid="stChatMessage"] pre {
    background: #1E293B !important;
    border-radius: 12px !important;
    padding: 1.1rem 1.25rem !important;
    margin: 0.75rem 0 !important;
    border: none !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.1) !important;
}
[data-testid="stChatMessage"] pre code {
    background: transparent !important;
    color: #93C5FD !important;
    border: none !important;
    padding: 0 !important;
    font-size: 0.85rem !important;
    line-height: 1.65 !important;
}

/* ═══════ CHAT INPUT ═══════ */
[data-testid="stChatInput"] {
    background: #FFFFFF !important;
    border: 2px solid #BFDBFE !important;
    border-radius: 16px !important;
    box-shadow: 0 4px 16px rgba(59,130,246,0.06) !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
    overflow: hidden !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: #3B82F6 !important;
    box-shadow: 0 0 0 4px rgba(59,130,246,0.1), 0 4px 16px rgba(59,130,246,0.06) !important;
}
[data-testid="stChatInput"] > div,
[data-testid="stChatInput"] > div > div,
[data-testid="stChatInput"] > div > div > div,
[data-testid="stChatInput"] [data-baseweb],
[data-testid="stChatInput"] [class*="InputContainer"],
[data-testid="stChatInput"] [class*="Root"],
[data-testid="stChatInput"] [class*="isFocused"] {
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    background: transparent !important;
}
[data-testid="stChatInput"] textarea {
    background: transparent !important;
    background-color: transparent !important;
    color: #0F172A !important;
    -webkit-text-fill-color: #0F172A !important;
    caret-color: #3B82F6 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.93rem !important;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    padding: 0.85rem 1rem !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: #94A3B8 !important;
    -webkit-text-fill-color: #94A3B8 !important;
}
[data-testid="stChatInput"] button {
    background: #3B82F6 !important;
    border: none !important;
    border-radius: 12px !important;
    margin: 6px 8px 6px 0 !important;
    min-width: 40px !important;
    height: 40px !important;
    transition: background 0.15s, transform 0.12s !important;
    box-shadow: 0 2px 8px rgba(59,130,246,0.3) !important;
}
[data-testid="stChatInput"] button:hover {
    background: #2563EB !important;
    transform: scale(1.06) !important;
}
[data-testid="stChatInput"] button svg { fill: #FFFFFF !important; }

/* ═══════ EXAMPLE PROMPT CARDS ═══════ */
.ex-card .stButton > button {
    background: #FFFFFF !important;
    color: #475569 !important;
    border: 1.5px solid #E2E8F0 !important;
    border-radius: 12px !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    padding: 0.7rem 1rem !important;
    width: 100% !important;
    text-align: left !important;
    line-height: 1.4 !important;
    transition: all 0.18s ease !important;
    font-family: 'Inter', sans-serif !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
}
.ex-card .stButton > button:hover {
    background: #EFF6FF !important;
    border-color: #3B82F6 !important;
    color: #1D4ED8 !important;
    box-shadow: 0 4px 14px rgba(59,130,246,0.12) !important;
    transform: translateY(-2px) !important;
}

/* ═══════ METRICS ═══════ */
[data-testid="stMetric"] {
    background: #EFF6FF !important;
    border: 1px solid #DBEAFE !important;
    border-radius: 12px !important;
    padding: 0.6rem 0.85rem !important;
}
[data-testid="stMetricValue"] {
    color: #2563EB !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 700 !important;
    font-size: 1.2rem !important;
}
[data-testid="stMetricLabel"] p {
    color: #94A3B8 !important;
    font-size: 0.68rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}

/* Progress bar */
[data-testid="stProgressBar"] > div > div {
    background: #DBEAFE !important;
    border-radius: 999px !important;
    height: 5px !important;
}
[data-testid="stProgressBar"] > div > div > div {
    background: linear-gradient(90deg, #3B82F6, #60A5FA) !important;
    border-radius: 999px !important;
}

/* Misc */
hr { border: none !important; border-top: 1px solid #DBEAFE !important; margin: 0.75rem 0 !important; }
[data-testid="stCaptionContainer"] p { color: #94A3B8 !important; font-size: 0.72rem !important; }
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #BFDBFE; border-radius: 999px; }
::-webkit-scrollbar-thumb:hover { background: #3B82F6; }
</style>
""", unsafe_allow_html=True)


# ═══════ SIDEBAR ═══════
with st.sidebar:
    # Logo
    st.markdown("""
    <div style="display:flex;align-items:center;gap:12px;padding:0 0 1rem">
        <div style="width:38px;height:38px;background:linear-gradient(135deg,#3B82F6,#60A5FA);
                    border-radius:12px;display:flex;align-items:center;justify-content:center;
                    font-size:1.15rem;flex-shrink:0;box-shadow:0 3px 10px rgba(59,130,246,0.3)">🔍</div>
        <div>
            <div style="font-weight:800;font-size:1.05rem;color:#0F172A;letter-spacing:-0.02em">CodeLens</div>
            <div style="font-size:0.72rem;color:#94A3B8;margin-top:1px">AI Code Explainer</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Model
    st.markdown('<p style="font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#94A3B8;margin:0 0 6px">Model</p>', unsafe_allow_html=True)
    model_choice = st.selectbox("Model", ["qwen2.5:0.5b", "codellama:7b", "phi3:latest"], index=0, label_visibility="collapsed")

    # Temperature
    st.markdown('<p style="font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#94A3B8;margin:0.75rem 0 6px">Temperature</p>', unsafe_allow_html=True)
    temperature = st.slider("Temp", 0.0, 1.0, 0.2, 0.05, label_visibility="collapsed")
    temp_desc = "precise" if temperature < 0.4 else "balanced" if temperature < 0.7 else "creative"
    st.markdown(f'<p style="font-size:0.7rem;color:#94A3B8;text-align:right;margin-top:-6px">{temperature:.2f} · {temp_desc}</p>', unsafe_allow_html=True)

    st.markdown("---")

    # Clear chat
    if st.button("🗑️  Clear conversation", use_container_width=True):
        for k in ["service", "messages", "_model"]:
            st.session_state.pop(k, None)
        st.rerun()

    st.markdown("---")

    # How to use
    st.markdown('<p style="font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#94A3B8;margin:0 0 8px">How to use</p>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:0.8rem;color:#64748B;line-height:2">
        1. Paste any code snippet<br>
        2. Hit <b style="color:#3B82F6">Enter</b> or click send<br>
        3. Ask follow-up questions<br>
        4. Use <b style="color:#3B82F6">Clear</b> to start fresh
    </div>
    """, unsafe_allow_html=True)


# ═══════ SESSION STATE ═══════
if "service" not in st.session_state or st.session_state.get("_model") != model_choice:
    st.session_state.service = ChatService(model=model_choice, temperature=temperature)
    st.session_state._model = model_choice
    st.session_state.messages = []

if "messages" not in st.session_state:
    st.session_state.messages = []

service: ChatService = st.session_state.service
service.temperature = temperature


# ═══════ HEADER ═══════
st.markdown("""
<div style="text-align:center;padding:0.5rem 0 0.5rem">
    <h1 style="font-size:1.5rem;font-weight:800;color:#0F172A;margin:0;letter-spacing:-0.04em">
        🔍 CodeLens
    </h1>
    <p style="font-size:0.88rem;color:#94A3B8;margin:0.2rem 0 0;font-weight:400">
        Understand code, one explanation at a time.
    </p>
</div>
""", unsafe_allow_html=True)
st.markdown("---")


# ═══════ EMPTY STATE — hero + example buttons ═══════
EXAMPLES = [
    ("🐍", "Explain this Python function"),
    ("🐛", "Find bugs in my JavaScript"),
    ("🗄️", "Explain this SQL query"),
    ("🐚", "What does this Bash script do?"),
    ("🔁", "Help me understand recursion"),
]

example_prompt = None

if not st.session_state.messages:
    st.markdown("""
    <div style="text-align:center;padding:1.5rem 0 1.25rem">
        <p style="font-size:1.1rem;font-weight:600;color:#334155;margin:0 0 0.3rem">
            Paste any code snippet and get a clear explanation.
        </p>
        <p style="font-size:0.85rem;color:#94A3B8;margin:0">
            Or try one of these examples:
        </p>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(len(EXAMPLES))
    for i, (icon, label) in enumerate(EXAMPLES):
        with cols[i]:
            st.markdown('<div class="ex-card">', unsafe_allow_html=True)
            if st.button(f"{icon} {label}", key=f"ex_{i}", use_container_width=True):
                example_prompt = label
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="height:1.5rem"></div>', unsafe_allow_html=True)


# ═══════ CHAT HISTORY ═══════
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ═══════ HANDLE INPUT ═══════
def handle(user_text: str) -> None:
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)
    with st.chat_message("assistant"):
        reply = st.write_stream(service.stream(user_text))
    st.session_state.messages.append({"role": "assistant", "content": reply})


if example_prompt:
    handle(example_prompt)
    st.rerun()

if prompt := st.chat_input("Paste code or ask a question…"):
    handle(prompt)
    st.rerun()


# ═══════ TOKEN USAGE (sidebar bottom) ═══════
with st.sidebar:
    st.markdown("---")
    st.markdown('<p style="font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#94A3B8;margin:0 0 8px">Token Usage</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    c1.metric("Input", f"{service.total_input_tokens:,}")
    c2.metric("Output", f"{service.total_output_tokens:,}")
    total = service.total_input_tokens + service.total_output_tokens
    if total > 0:
        st.progress(min(total / 10_000, 1.0))
    st.caption(f"{total:,} tokens · local · free")
