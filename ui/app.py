import sys
import os
import uuid
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ui.api_helper import (
    ask_question, resume_action,
    login_user, register_user,
    list_threads, create_thread, load_conversation,
    API_BASE_URL,
)

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
    /* ── Base ─────────────────────────────────────────────────────────── */
    .stApp { background-color: #0b0b0e; color: #f1f1f1; }

    section[data-testid="stSidebar"] {
        background-color: #121217;
        border-right: 1px solid #291013;
    }
    h1, h2, h3, h4 { color: #ff3344 !important; font-family: 'Inter', sans-serif; }

    /* ── Chat messages ─────────────────────────────────────────────────── */
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

    /* ── HITL box ──────────────────────────────────────────────────────── */
    .hitl-box {
        background: linear-gradient(145deg, #1f0d11 0%, #15151c 100%);
        border: 2px solid #e50914;
        border-radius: 14px;
        padding: 20px;
        margin: 15px 0px;
        box-shadow: 0 4px 20px rgba(229, 9, 20, 0.25);
    }
    .hitl-title {
        color: #ff4d5a; font-weight: 700; font-size: 1.15rem;
        margin-bottom: 10px; display: flex; align-items: center; gap: 8px;
    }

    /* ── Buttons ───────────────────────────────────────────────────────── */
    .stButton > button {
        border-radius: 8px; font-weight: 600; transition: all 0.2s ease-in-out;
    }
    div.stButton > button[kind="primary"] {
        background-color: #e50914; color: white; border: none;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #ff2233; box-shadow: 0 0 10px rgba(229, 9, 20, 0.5);
    }
    div.stButton > button[kind="secondary"] {
        background-color: #22222b; color: #ff6b76; border: 1px solid #4a1d23;
    }
    div.stButton > button[kind="secondary"]:hover {
        background-color: #33151b; color: #ff3344; border-color: #e50914;
    }

    /* ── Chat input ────────────────────────────────────────────────────── */
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

    /* ── Thread list items ─────────────────────────────────────────────── */
    .thread-btn > button {
        background-color: #1a1a24 !important;
        color: #cccccc !important;
        border: 1px solid #2a2a38 !important;
        border-radius: 8px !important;
        text-align: left !important;
        padding: 8px 12px !important;
        margin-bottom: 4px !important;
        font-size: 0.85rem !important;
        width: 100% !important;
    }
    .thread-btn > button:hover {
        background-color: #26131a !important;
        border-color: #e50914 !important;
        color: #ff6b76 !important;
    }
    .thread-btn-active > button {
        background-color: #2a0d12 !important;
        border-color: #e50914 !important;
        color: #ff4455 !important;
        font-weight: 700 !important;
    }

    /* ── Auth card ─────────────────────────────────────────────────────── */
    .auth-logo { font-size: 3rem; text-align: center; margin-bottom: 6px; }
    .auth-title {
        font-size: 1.6rem; font-weight: 800;
        color: #ff3344 !important; text-align: center; margin-bottom: 2px;
    }
    .auth-subtitle { font-size: 0.85rem; color: #888; text-align: center; margin-bottom: 28px; }

    /* ── Inputs ────────────────────────────────────────────────────────── */
    div[data-testid="stTextInput"] input {
        background-color: #0f0f16 !important;
        color: #f1f1f1 !important;
        border: 1px solid #3d1419 !important;
        border-radius: 8px !important;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: #e50914 !important;
        box-shadow: 0 0 6px rgba(229, 9, 20, 0.35) !important;
    }

    /* ── Tabs ──────────────────────────────────────────────────────────── */
    button[data-baseweb="tab"] { color: #888 !important; font-weight: 600 !important; }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #ff3344 !important;
        border-bottom: 2px solid #e50914 !important;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. Session State Initialization
# -----------------------------------------------------------------------------
for key, default in [
    ("logged_in", False),
    ("access_token", None),
    ("user_email", None),
    ("thread_id", None),
    ("messages", []),
    ("pending_hitl", None),
    ("threads", []),           # list of ThreadOut dicts from the API
    ("threads_loaded", False), # guard so we only fetch once per login
]:
    if key not in st.session_state:
        st.session_state[key] = default


# -----------------------------------------------------------------------------
# 3. Auth Page
# -----------------------------------------------------------------------------
def render_auth_page():
    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        st.markdown('<div class="auth-logo">🤖</div>', unsafe_allow_html=True)
        st.markdown('<p class="auth-title">Major1 AI Assistant</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="auth-subtitle">Enterprise Agentic RAG · MCP · LangGraph</p>',
            unsafe_allow_html=True,
        )

        login_tab, register_tab = st.tabs(["🔑  Login", "📝  Register"])

        # ── Login ──────────────────────────────────────────────────────────
        with login_tab:
            st.markdown("<br>", unsafe_allow_html=True)
            email    = st.text_input("Email",    key="login_email",    placeholder="you@example.com")
            password = st.text_input("Password", key="login_password", type="password", placeholder="••••••••")
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Login →", type="primary", use_container_width=True, key="btn_login"):
                if not email or not password:
                    st.error("Please enter your email and password.")
                else:
                    with st.spinner("Authenticating…"):
                        result = login_user(email, password)
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        _set_logged_in(result["access_token"], email)
                        st.success("✅ Logged in! Redirecting…")
                        st.rerun()

        # ── Register ────────────────────────────────────────────────────────
        with register_tab:
            st.markdown("<br>", unsafe_allow_html=True)
            reg_email   = st.text_input("Email",            key="reg_email",    placeholder="you@example.com")
            reg_password = st.text_input("Password",        key="reg_password", type="password", placeholder="Min 8 characters")
            reg_confirm  = st.text_input("Confirm Password",key="reg_confirm",  type="password", placeholder="Repeat password")
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Create Account →", type="primary", use_container_width=True, key="btn_register"):
                if not reg_email or not reg_password or not reg_confirm:
                    st.error("Please fill in all fields.")
                elif reg_password != reg_confirm:
                    st.error("Passwords do not match.")
                elif len(reg_password) < 8:
                    st.error("Password must be at least 8 characters.")
                else:
                    with st.spinner("Creating your account…"):
                        result = register_user(reg_email, reg_password)
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        _set_logged_in(result["access_token"], reg_email)
                        st.success("🎉 Account created! Redirecting…")
                        st.rerun()


def _set_logged_in(token: str, email: str):
    """Populate session state after a successful auth."""
    st.session_state.logged_in      = True
    st.session_state.access_token   = token
    st.session_state.user_email     = email
    st.session_state.messages       = []
    st.session_state.pending_hitl   = None
    st.session_state.threads        = []
    st.session_state.threads_loaded = False
    st.session_state.thread_id      = None


# -----------------------------------------------------------------------------
# 4. Sidebar — thread list helpers
# -----------------------------------------------------------------------------
def _refresh_threads():
    """Fetch the thread list from the API and store in session state."""
    result = list_threads(st.session_state.access_token)
    if "error" not in result:
        st.session_state.threads = result.get("threads", [])
    st.session_state.threads_loaded = True


def _new_conversation():
    """Create a new thread via the API, activate it, and refresh the list."""
    result = create_thread("New Conversation", token=st.session_state.access_token)
    if "error" in result:
        st.error(result["error"])
        return
    new_id = str(result["thread_id"])
    st.session_state.thread_id    = new_id
    st.session_state.messages     = []
    st.session_state.pending_hitl = None
    _refresh_threads()


def _switch_thread(thread_id: str):
    """Load history for a thread and make it active."""
    if st.session_state.thread_id == thread_id:
        return  # already active — no-op
    history = load_conversation(thread_id, token=st.session_state.access_token)
    st.session_state.thread_id    = thread_id
    st.session_state.messages     = history   # [{role, content}, ...]
    st.session_state.pending_hitl = None


# -----------------------------------------------------------------------------
# 5. Chat Page
# -----------------------------------------------------------------------------
def render_chat_page():
    token = st.session_state.access_token

    # Fetch threads once per login session
    if not st.session_state.threads_loaded:
        _refresh_threads()
        # If there are no threads yet, create the first one automatically
        if not st.session_state.threads:
            _new_conversation()
        else:
            # Activate the most-recent thread
            st.session_state.thread_id = str(st.session_state.threads[0]["thread_id"])
            history = load_conversation(st.session_state.thread_id, token=token)
            st.session_state.messages = history

    # ── Sidebar ────────────────────────────────────────────────────────────
    with st.sidebar:
        st.title("🔴 Major 1 Control")
        st.caption("Enterprise Agentic RAG with MCP & LangGraph")
        st.markdown("---")

        # Account
        st.markdown("### 👤 Account")
        st.markdown(f"**{st.session_state.user_email}**")
        if st.button("🚪 Logout", use_container_width=True, key="btn_logout"):
            for k in ["logged_in", "access_token", "user_email",
                      "messages", "pending_hitl", "threads",
                      "threads_loaded", "thread_id"]:
                st.session_state[k] = (
                    False if k == "logged_in"
                    else [] if k in ("messages", "threads")
                    else None
                )
            st.session_state.threads_loaded = False
            st.rerun()

        st.markdown("---")

        # New Conversation
        st.markdown("### 💬 Conversations")
        if st.button("➕  New Conversation", type="primary", use_container_width=True):
            _new_conversation()
            st.rerun()

        # Thread list
        threads = st.session_state.threads
        active  = str(st.session_state.thread_id) if st.session_state.thread_id else ""

        if not threads:
            st.caption("No conversations yet.")
        else:
            for t in threads:
                tid   = str(t["thread_id"])
                title = t.get("thread_title", "Untitled")
                css   = "thread-btn-active" if tid == active else "thread-btn"
                # Wrap in a div to apply the CSS class
                st.markdown(f'<div class="{css}">', unsafe_allow_html=True)
                if st.button(f"🗨️ {title}", key=f"thread_{tid}", use_container_width=True):
                    _switch_thread(tid)
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 🔌 Backend & Session")
        st.markdown(f"**Backend:** `{API_BASE_URL}`")
        if st.session_state.thread_id:
            st.markdown("**Active Thread:**")
            st.code(st.session_state.thread_id, language="text")

        st.markdown("---")
        st.markdown("### 🛡️ Guardrails & Memory")
        st.info(
            "• **Persistent Memory:** The agent remembers context across turns.\n\n"
            "• **HITL Review:** High-risk actions require interactive approval.\n\n"
            "• **PII Redaction:** Sensitive details are masked automatically."
        )

    # ── Main Header ────────────────────────────────────────────────────────
    st.title("🤖 Live RAG Assistant")
    st.caption("Powered by LangGraph (MemorySaver), MCP Servers (Gmail & GitHub), and Groq LLaMA-3")

    # ── Chat History ───────────────────────────────────────────────────────
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ── HITL Approval Box ──────────────────────────────────────────────────
    if st.session_state.pending_hitl:
        hitl      = st.session_state.pending_hitl
        thread_id = hitl["thread_id"]
        event     = hitl["hitl_event"]
        tool_name = event.get("tool_name", "Unknown Action")
        args      = event.get("args", {})

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
                    res = resume_action(thread_id, "yes", token=token)
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
                    res = resume_action(thread_id, "no", token=token)
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

    # ── Chat Input ─────────────────────────────────────────────────────────
    is_pending = st.session_state.pending_hitl is not None
    prompt_placeholder = (
        "Approve or Reject the pending action above…"
        if is_pending
        else "Ask anything (e.g., 'What was my last email?', 'Send email to…')"
    )

    if user_input := st.chat_input(placeholder=prompt_placeholder, disabled=is_pending):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Agent is reasoning & recalling conversation..."):
                response = ask_question(
                    user_input,
                    thread_id=st.session_state.thread_id,
                    token=token,
                )

        if response.get("status") == "done":
            answer = response.get("answer", "")
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()
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


# -----------------------------------------------------------------------------
# 6. Router — auth gate
# -----------------------------------------------------------------------------
if not st.session_state.logged_in:
    render_auth_page()
else:
    render_chat_page()