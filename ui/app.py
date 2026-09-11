import sys
import os
import uuid
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ui.api_helper import ask_question, resume_action, API_BASE_URL

# -----------------------------------------------------------------------------
# 1. Page Configuration & Custom Red/Black Theme
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Major1 AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp {
        background-color: #0b0b0e;
        color: #f1f1f1;
    }
    section[data-testid="stSidebar"] {
        background-color: #121217;
        border-right: 1px solid #291013;
    }
    h1, h2, h3, h4 {
        color: #ff3344 !important;
        font-family: 'Inter', sans-serif;
    }
    .stChatMessage {
        background-color: #15151c;
        border-radius: 12px;
        border: 1px solid #2a181c;
        margin-bottom: 12px;
        padding: 14px;
    }
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) {
        background-color: #1c1316;
        border-left: 3px solid #e50914;
    }
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarAssistant"]) {
        background-color: #13141a;
        border-left: 3px solid #ff3344;
    }
    .hitl-box {
        background: linear-gradient(145deg, #1f0d11 0%, #15151c 100%);
        border: 2px solid #e50914;
        border-radius: 14px;
        padding: 20px;
        margin: 15px 0px;
        box-shadow: 0 4px 20px rgba(229, 9, 20, 0.25);
    }
    .hitl-title {
        color: #ff4d5a;
        font-weight: 700;
        font-size: 1.15rem;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
    }
    div.stButton > button[kind="primary"] {
        background-color: #e50914;
        color: white;
        border: none;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #ff2233;
        box-shadow: 0 0 10px rgba(229, 9, 20, 0.5);
    }
    div.stButton > button[kind="secondary"] {
        background-color: #22222b;
        color: #ff6b76;
        border: 1px solid #4a1d23;
    }
    div.stButton > button[kind="secondary"]:hover {
        background-color: #33151b;
        color: #ff3344;
        border-color: #e50914;
    }
    .stChatInputContainer textarea {
        background-color: #15151c !important;
        color: #ffffff !important;
        border: 1px solid #3d1419 !important;
        border-radius: 10px !important;
    }
    .stChatInputContainer textarea:focus {
        border-color: #e50914 !important;
        box-shadow: 0 0 8px rgba(229, 9, 20, 0.4) !important;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. Session State Initialization (Persistent thread_id per session)
# -----------------------------------------------------------------------------
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_hitl" not in st.session_state:
    st.session_state.pending_hitl = None

# -----------------------------------------------------------------------------
# 3. Sidebar Configuration
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("🔴 Major 1 Control")
    st.caption("Enterprise Agentic RAG with MCP & LangGraph")
    st.markdown("---")

    st.markdown("### 🔌 Backend & Session")
    st.markdown(f"**Backend:** `{API_BASE_URL}`")
    st.markdown(f"**Session Thread ID:**")
    st.code(st.session_state.thread_id, language="text")

    if st.button("🗑️ New Conversation", use_container_width=True, help="Starts a fresh memory thread"):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.session_state.pending_hitl = None
        st.rerun()

    st.markdown("---")
    st.markdown("### 🛡️ Guardrails & Memory")
    st.info(
        "• **Persistent Memory:** The agent remembers context across multiple turns in this session thread.\n\n"
        "• **HITL Review:** High-risk actions require interactive approval.\n\n"
        "• **PII Redaction:** Sensitive details are masked automatically."
    )

# -----------------------------------------------------------------------------
# 4. Main Chat Header
# -----------------------------------------------------------------------------
st.title("🤖 Live RAG Assistant")
st.caption("Powered by LangGraph (MemorySaver), MCP Servers (Gmail & GitHub), and Groq LLaMA-3")

# -----------------------------------------------------------------------------
# 5. Display Existing Chat Messages
# -----------------------------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -----------------------------------------------------------------------------
# 6. HITL Action Approval Box
# -----------------------------------------------------------------------------
if st.session_state.pending_hitl:
    hitl = st.session_state.pending_hitl
    thread_id = hitl["thread_id"]
    event = hitl["hitl_event"]
    tool_name = event.get("tool_name", "Unknown Action")
    args = event.get("args", {})

    st.markdown(f"""
    <div class="hitl-box">
        <div class="hitl-title">⚠️ High-Risk Action Approval Required</div>
        <p>The assistant wants to execute the following tool with your permission:</p>
        <p><b>Tool:</b> <code>{tool_name}</code></p>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("🔍 View Action Parameters", expanded=True):
        st.json(args)

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("✅ Approve Action", key="btn_approve", type="primary", use_container_width=True):
            with st.spinner("Executing approved action..."):
                res = resume_action(thread_id, "yes")
                if res.get("status") == "done":
                    answer = res.get("answer", "Action completed.")
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                    st.session_state.pending_hitl = None
                    st.rerun()
                elif res.get("status") == "pending":
                    st.session_state.pending_hitl = {
                        "thread_id": res["thread_id"],
                        "hitl_event": res["hitl_event"],
                    }
                    st.rerun()
                else:
                    st.error(res.get("answer", "An error occurred."))

    with col2:
        if st.button("❌ Reject Action", key="btn_reject", type="secondary", use_container_width=True):
            with st.spinner("Rejecting action and resuming agent..."):
                res = resume_action(thread_id, "no")
                if res.get("status") == "done":
                    answer = res.get("answer", "Action was rejected.")
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                    st.session_state.pending_hitl = None
                    st.rerun()
                elif res.get("status") == "pending":
                    st.session_state.pending_hitl = {
                        "thread_id": res["thread_id"],
                        "hitl_event": res["hitl_event"],
                    }
                    st.rerun()
                else:
                    st.error(res.get("answer", "An error occurred."))

# -----------------------------------------------------------------------------
# 7. Chat Input Field
# -----------------------------------------------------------------------------
is_pending = st.session_state.pending_hitl is not None
prompt_placeholder = "Approve or Reject the pending action above..." if is_pending else "Ask anything (e.g., 'What was my last email?', 'Send email to...')"

if user_input := st.chat_input(placeholder=prompt_placeholder, disabled=is_pending):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Agent is reasoning & recalling conversation..."):
            response = ask_question(user_input, thread_id=st.session_state.thread_id)

        if response.get("status") == "done":
            answer = response.get("answer", "")
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
        elif response.get("status") == "pending":
            st.session_state.pending_hitl = {
                "thread_id": response["thread_id"],
                "hitl_event": response["hitl_event"],
            }
            st.rerun()
        else:
            err_msg = response.get("answer", "Error communicating with backend.")
            st.error(err_msg)
            st.session_state.messages.append({"role": "assistant", "content": err_msg})