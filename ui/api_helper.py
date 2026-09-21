from dotenv import load_dotenv
load_dotenv()
import os

# Try environment variable first, then Streamlit Cloud secrets
API_BASE_URL = os.getenv("API_BASE_URL")
if not API_BASE_URL:
    try:
        import streamlit as st
        API_BASE_URL = st.secrets.get("API_BASE_URL")
    except Exception:
        pass
if not API_BASE_URL:
    API_BASE_URL = "http://127.0.0.1:8000"

# Strip any trailing slash so f"{API_BASE_URL}/path" doesn't produce double slashes
API_BASE_URL = API_BASE_URL.rstrip("/")



# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def login_user(email: str, password: str) -> Dict[str, Any]:
    """POST /auth/login  →  {"access_token": "..."} or {"error": "..."}"""
    url = f"{API_BASE_URL}/auth/login"
    try:
        response = requests.post(url, json={"email": email, "password": password}, timeout=15)
        if response.status_code == 200:
            return {"access_token": response.json()["access_token"]}
        detail = response.json().get("detail", "Login failed.")
        return {"error": detail}
    except requests.exceptions.ConnectionError:
        return {"error": f"❌ Cannot reach backend at {API_BASE_URL}. Is FastAPI running?"}
    except requests.exceptions.RequestException as e:
        return {"error": f"❌ Request error: {str(e)}"}


def register_user(email: str, password: str) -> Dict[str, Any]:
    """POST /auth/register  →  {"access_token": "..."} or {"error": "..."}"""
    url = f"{API_BASE_URL}/auth/register"
    try:
        response = requests.post(url, json={"email": email, "password": password}, timeout=15)
        if response.status_code == 201:
            return {"access_token": response.json()["access_token"]}
        detail = response.json().get("detail", "Registration failed.")
        return {"error": detail}
    except requests.exceptions.ConnectionError:
        return {"error": f"❌ Cannot reach backend at {API_BASE_URL}. Is FastAPI running?"}
    except requests.exceptions.RequestException as e:
        return {"error": f"❌ Request error: {str(e)}"}


# ---------------------------------------------------------------------------
# Thread helpers
# ---------------------------------------------------------------------------

def list_threads(token: str) -> Dict[str, Any]:
    """GET /threads  →  {"threads": [...]} or {"error": "..."}"""
    url = f"{API_BASE_URL}/threads"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json()           # {"threads": [...]}
        detail = response.json().get("detail", "Failed to fetch threads.")
        return {"error": detail}
    except requests.exceptions.ConnectionError:
        return {"error": f"❌ Cannot reach backend at {API_BASE_URL}."}
    except requests.exceptions.RequestException as e:
        return {"error": f"❌ {str(e)}"}


def create_thread(title: str = "New Conversation", token: str = "") -> Dict[str, Any]:
    """POST /threads  →  ThreadOut dict or {"error": "..."}"""
    url = f"{API_BASE_URL}/threads"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.post(url, json={"thread_title": title}, headers=headers, timeout=15)
        if response.status_code == 201:
            return response.json()           # {thread_id, thread_title, ...}
        detail = response.json().get("detail", "Failed to create thread.")
        return {"error": detail}
    except requests.exceptions.ConnectionError:
        return {"error": f"❌ Cannot reach backend at {API_BASE_URL}."}
    except requests.exceptions.RequestException as e:
        return {"error": f"❌ {str(e)}"}


def load_conversation(thread_id: str, token: str = "") -> List[Dict[str, str]]:
    """GET /chat/history/{thread_id}  →  list of {role, content} or []"""
    url = f"{API_BASE_URL}/chat/history/{thread_id}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()           # [{role, content}, ...]
        return []
    except requests.exceptions.RequestException:
        return []


# ---------------------------------------------------------------------------
# Chat helpers
# ---------------------------------------------------------------------------

def ask_question(
    question: str,
    thread_id: Optional[str] = None,
    token: Optional[str] = None,
) -> Dict[str, Any]:
    """POST /chat/ask — send a question with the persistent session thread_id."""
    url = f"{API_BASE_URL}/chat/ask"
    payload = {"question": question}
    if thread_id:
        payload["thread_id"] = thread_id

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return {
            "status": "error",
            "answer": f"❌ Could not connect to backend at {API_BASE_URL}. Please ensure FastAPI is running.",
            "thread_id": thread_id or "",
            "hitl_event": None,
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "answer": f"❌ Error communicating with backend: {str(e)}",
            "thread_id": thread_id or "",
            "hitl_event": None,
        }


def resume_action(
    thread_id: str,
    approval: str,
    token: Optional[str] = None,
) -> Dict[str, Any]:
    """POST /chat/resume — resume a paused HITL execution."""
    url = f"{API_BASE_URL}/chat/resume"
    payload = {"thread_id": thread_id, "approval": approval}

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return {
            "status": "error",
            "answer": f"❌ Could not connect to backend at {API_BASE_URL}. Please ensure FastAPI is running.",
            "thread_id": thread_id,
            "hitl_event": None,
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "answer": f"❌ Error resuming action: {str(e)}",
            "thread_id": thread_id,
            "hitl_event": None,
        }